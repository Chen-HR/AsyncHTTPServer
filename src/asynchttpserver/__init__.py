import abc
import asyncio
import logging
import time

try:
  from .Status import Status
  from .Method import Method
  from .Message import RequestMessage, ResponseMessage
except ImportError:
  from asynchttpserver.Status import Status
  from asynchttpserver.Method import Method
  from asynchttpserver.Message import RequestMessage, ResponseMessage

# Configuration limits to prevent OOM on microcontrollers
MAX_HEADER_SIZE = 4096  # 4KB limit for headers
MAX_BODY_SIZE = 1024 * 64 # 64KB limit for body (adjust based on RAM)
READ_TIMEOUT = 10 # Seconds

class AsyncRequestHandler(abc.ABC):
  """Abstract base class for handling asynchronous HTTP requests."""
  @abc.abstractmethod
  async def handle(self, request: RequestMessage) -> ResponseMessage:
    """
    Processes an incoming RequestMessage and returns a ResponseMessage.
    """
    pass

class AsyncRequestResponseHandler(AsyncRequestHandler):
  """A concrete request handler that uses a callback to generate a response."""
  def __init__(self, callback):
    self._callback = callback

  async def handle(self, request: RequestMessage) -> ResponseMessage:
    return await self._callback(request)

class AsyncRequestRouteHandler(AsyncRequestHandler):
  """
  A request handler that routes requests to other handlers based on path and method.
  """
  def __init__(self, logger: logging.Logger | None = None):
    # Structure: { "GET": {"/path": handler}, ... }
    self._routes: dict[str, dict[str, AsyncRequestHandler]] = {}
    self.logger = logger

  def add_route(self, path: str, handler: AsyncRequestHandler, method: Method = Method.GET):
    method_name = method.name
    if method_name not in self._routes:
      self._routes[method_name] = {}
    self._routes[method_name][path] = handler

  async def handle(self, request: RequestMessage) -> ResponseMessage:
    method_routes = self._routes.get(request.method.name, {})
    
    # Find the best matching path
    # Rule: Path must match exactly OR be a parent path (e.g. /api matches /api/v1 but /api does not match /apiv1)
    best_match_path = ""
    handler = None
    
    for path, registered_handler in method_routes.items():
      # Check 1: Exact match
      if request.path == path:
        best_match_path = path
        handler = registered_handler
        break # Exact match is always best
      
      # Check 2: Prefix match (ensure directory boundary)
      # If path is "/", it matches everything
      if path == "/" or (request.path.startswith(path) and request.path[len(path)] == '/'):
        if len(path) > len(best_match_path):
          best_match_path = path
          handler = registered_handler
          
    if handler:
      if self.logger: self.logger.debug(f"Routing {request.method.name} {request.path} to {handler}")
      
      # Strip prefix from path for the sub-handler
      # Special case: if mapped to root "/", don't strip anything usually, or strip just the /?
      # Typically in micro-frameworks:
      # If mapped /api -> handler, and req is /api/users, sub-path is /users
      sub_path = request.path[len(best_match_path):]
      if not sub_path.startswith("/"):
          sub_path = "/" + sub_path
          
      # Create a shallow copy or new instance with modified path if needed
      # Here we modify the request object directly or create a new one. Creating new is safer.
      modified_request = RequestMessage(
        method=request.method,
        path=sub_path,
        header=request.header,
        body=request.body,
        version=request.version
      )
      return await handler.handle(modified_request)
    else:
      if self.logger: self.logger.debug(f"No route found for {request.method.name} {request.path}")
      return ResponseMessage(
        status=Status.NOT_FOUND,
        header={"Content-Type": "text/plain", "Connection": "close"},
        body=b"404 Not Found"
      )

class AsyncServer:
  """An asynchronous HTTP server that listens for and handles connections."""
  def __init__(self, root_handler: AsyncRequestHandler, host: str = '0.0.0.0', port: int = 80, logger: logging.Logger | None = None):
    self.root_handler = root_handler
    self.host = host
    self.port = port
    self.logger = logger
    self._server = None

  async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    if self.logger: self.logger.info(f"New connection from {addr}")

    try:
      # --- Step 1: Read Headers ---
      header_bytes = b""
      total_header_len = 0
      
      while True:
        # Read line by line with timeout
        try:
            line = await asyncio.wait_for(reader.readline(), READ_TIMEOUT)
        except asyncio.TimeoutError:
            if self.logger: self.logger.warning("Timeout waiting for headers")
            return # Close connection silently

        if not line: # EOF
          return

        total_header_len += len(line)
        if total_header_len > MAX_HEADER_SIZE:
           raise ValueError("Header too large")

        header_bytes += line
        
        # Check for end of headers (\r\n on a line by itself)
        if line == b'\r\n':
          break

      # --- Step 2: Parse Headers ---
      # This creates the RequestMessage with empty body
      request = RequestMessage.unpack_header(header_bytes)
      
      # --- Step 3: Read Body ---
      # 'content-length' is lowercase because Message normalizes headers
      content_len = int(request.header.get('content-length', 0))
      
      if content_len > MAX_BODY_SIZE:
          raise ValueError(f"Body too large ({content_len} > {MAX_BODY_SIZE})")
      
      if content_len > 0:
        try:
            body_data = await asyncio.wait_for(reader.readexactly(content_len), READ_TIMEOUT)
            request.body = body_data
        except asyncio.TimeoutError:
             if self.logger: self.logger.warning("Timeout waiting for body")
             return

      # --- Step 4: Handle Request ---
      response = await self.root_handler.handle(request)
      
      # --- Step 5: Send Response ---
      writer.write(response.pack())
      await writer.drain()

    except ValueError as e:
      if self.logger: self.logger.error(f"Invalid request: {e}")
      # Send 400 Bad Request
      err_resp = ResponseMessage(Status.BAD_REQUEST, {"Connection": "close"}, b"400 Bad Request")
      writer.write(err_resp.pack())
      await writer.drain()
      
    except Exception as e:
      if self.logger: self.logger.error(f"Internal Error: {e}")
      # Send 500 Internal Server Error
      err_resp = ResponseMessage(Status.INTERNAL_SERVER_ERROR, {"Connection": "close"}, b"500 Internal Server Error")
      writer.write(err_resp.pack())
      await writer.drain()
      
    finally:
      try:
        writer.close()
        await writer.wait_closed()
      except Exception:
        pass # Ignore errors during close
      if self.logger: self.logger.debug(f"Connection closed {addr}")

  async def start(self):
    """Starts the asyncio server."""
    if self._server:
      return
    
    self._server = await asyncio.start_server(self._handle_connection, self.host, self.port)
    if self.logger: self.logger.info(f"Server started on {self.host}:{self.port}")
    
    # In standard asyncio, start_server returns a Server object.
    # We generally don't block here, but we can if needed. 
    # To keep running indefinitely, the caller usually does `await asyncio.Event().wait()` or similar.

  async def stop(self):
    """Stops the asyncio server."""
    if self._server:
      self._server.close()
      await self._server.wait_closed()
      self._server = None
      if self.logger: self.logger.info("Server stopped")