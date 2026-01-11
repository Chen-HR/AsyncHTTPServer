import abc
import asyncio
import time
import os

try:
  from .Status import Status
  from .Method import Method
  from .Message import RequestMessage, ResponseMessage
  from .Mime import Mime
except ImportError:
  from asynchttpserver.Status import Status
  from asynchttpserver.Method import Method
  from asynchttpserver.Message import RequestMessage, ResponseMessage
  from asynchttpserver.Mime import Mime

# Configuration limits
MAX_HEADER_SIZE = 4096 
MAX_BODY_SIZE = 1024 * 64 
READ_TIMEOUT = 10 

class AsyncRequestHandler(abc.ABC):
  """Abstract base class for handling asynchronous HTTP requests."""
  @abc.abstractmethod
  async def handle(self, request: RequestMessage) -> ResponseMessage:
    pass

class AsyncRequestResponseHandler(AsyncRequestHandler):
  """A concrete request handler that uses a callback to generate a response."""
  def __init__(self, callback):
    self._callback = callback

  async def handle(self, request: RequestMessage) -> ResponseMessage:
    return await self._callback(request)

class AsyncStaticFileHandler(AsyncRequestHandler):
  """
  Handles serving static files from a directory using Mime class for content types.
  """
  def __init__(self, directory: str, default_file: str = "index.html"):
    self.directory = os.path.abspath(directory)
    self.default_file = default_file

  def _read_file_sync(self, path: str) -> bytes:
    with open(path, "rb") as f:
      return f.read()

  async def handle(self, request: RequestMessage) -> ResponseMessage:
    # 1. Determine relative path
    rel_path = request.path.lstrip("/")
    if not rel_path:
        rel_path = self.default_file
    
    # 2. Resolve full absolute path
    full_path = os.path.abspath(os.path.join(self.directory, rel_path))

    # 3. Security check: Prevent Directory Traversal
    if not full_path.startswith(self.directory):
        return ResponseMessage(Status.FORBIDDEN, {}, Status.FORBIDDEN.__str__().encode())

    # 4. Check existence
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return ResponseMessage(Status.NOT_FOUND, {}, Status.NOT_FOUND.__str__().encode())

    # 5. Read file and return response
    try:
        loop = asyncio.get_running_loop()
        # Use executor to avoid blocking the async event loop with file I/O
        content = await loop.run_in_executor(None, self._read_file_sync, full_path)
        
        # Use the new Mime helper
        content_type = Mime.guess_type(full_path)
        
        return ResponseMessage(
            status=Status.OK,
            header={"Content-Type": content_type},
            body=content
        )
    except Exception:
        return ResponseMessage(Status.INTERNAL_SERVER_ERROR, {}, Status.INTERNAL_SERVER_ERROR.__str__().encode())

class AsyncRequestRouteHandler(AsyncRequestHandler):
  """
  A request handler that routes requests to other handlers based on path and method.
  Supports Flask-like decorators and static file serving.
  """
  def __init__(self, logger=None):
    # Structure: { "GET": {"/path": handler}, ... }
    self._routes: dict[str, dict[str, AsyncRequestHandler]] = {}
    self.logger = logger

  def add_route(self, path: str, handler: AsyncRequestHandler, methods: list[Method] | None = None):
    """
    Registers a handler for a specific path and a list of methods.
    """
    if methods is None:
      methods = [Method.GET]
      
    for method in methods:
      if self.logger: self.logger.debug(f"Registering route {method.name} {path}")
      method_name = method.name
      if method_name not in self._routes:
        self._routes[method_name] = {}
      self._routes[method_name][path] = handler

  def route(self, path: str, methods: list[Method] = [Method.GET]):
    """
    Decorator to register a function as a route handler.
    """
    def decorator(handler):
      _handler = AsyncRequestResponseHandler(handler)
      self.add_route(path, _handler, methods)
      return handler
    return decorator

  def mount(self, path: str, methods: list[Method] = [Method.GET]):
    """
    Decorator to mount a Sub-Router (or any AsyncRequestHandler).
    """
    def decorator(func):
      handler = func()
      if not isinstance(handler, AsyncRequestHandler):
          raise TypeError(f"Mounted function {func.__name__} must return an AsyncRequestHandler")
      self.add_route(path, handler, methods)
      return handler
    return decorator

  def static(self, path: str, directory: str, default_file: str = "index.html"):
    """
    Registers a static file handler for the given URL path.
    """
    handler = AsyncStaticFileHandler(directory, default_file)
    self.add_route(path, handler, [Method.GET])

  async def handle(self, request: RequestMessage) -> ResponseMessage:
    method_routes = self._routes.get(request.method.name, {})
    
    best_match_path = ""
    handler = None
    
    for path, registered_handler in method_routes.items():
      if request.path == path:
        best_match_path = path
        handler = registered_handler
        break 
      
      # Prefix matching logic
      if path == "/" or (request.path.startswith(path) and request.path[len(path)] == '/'):
        if len(path) > len(best_match_path):
          best_match_path = path
          handler = registered_handler
          
    if handler:
      if self.logger: self.logger.debug(f"Routing {request.method.name} {request.path} to {handler}")
      
      # Strip the prefix path for the sub-handler
      sub_path = request.path[len(best_match_path):]
      if not sub_path.startswith("/"):
          sub_path = "/" + sub_path
          
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
        header={"Content-Type": Mime.TXT, "Connection": "close"},
        body=Status.NOT_FOUND.__str__().encode()
      )

class AsyncServer:
  """An asynchronous HTTP server."""
  def __init__(self, root_handler: AsyncRequestHandler, host: str = '0.0.0.0', port: int = 80, logger=None):
    self.root_handler = root_handler
    self.host = host
    self.port = port
    self.logger = logger
    self._server = None

  async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    if self.logger: self.logger.info(f"New connection from {addr}")

    try:
      header_bytes = b""
      total_header_len = 0
      
      while True:
        try:
            line = await asyncio.wait_for(reader.readline(), READ_TIMEOUT)
        except asyncio.TimeoutError:
            if self.logger: self.logger.warning("Timeout waiting for headers")
            return 

        if not line: return

        total_header_len += len(line)
        if total_header_len > MAX_HEADER_SIZE:
           raise ValueError("Header too large")

        header_bytes += line
        if line == b'\r\n':
          break

      request = RequestMessage.unpack_header(header_bytes)
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

      response = await self.root_handler.handle(request)
      
      writer.write(response.pack())
      await writer.drain()

    except ValueError as e:
      if self.logger: self.logger.error(f"Invalid request: {e}")
      err_resp = ResponseMessage(Status.BAD_REQUEST, {"Connection": "close"}, Status.BAD_REQUEST.__str__().encode())
      writer.write(err_resp.pack())
      await writer.drain()
      
    except Exception as e:
      if self.logger: self.logger.error(f"Internal Error: {e}")
      err_resp = ResponseMessage(Status.INTERNAL_SERVER_ERROR, {"Connection": "close"}, Status.INTERNAL_SERVER_ERROR.__str__().encode())
      writer.write(err_resp.pack())
      await writer.drain()
      
    finally:
      try:
        writer.close()
        await writer.wait_closed()
      except Exception:
        pass
      if self.logger: self.logger.debug(f"Connection closed {addr}")

  async def start(self):
    if self._server: return
    self._server = await asyncio.start_server(self._handle_connection, self.host, self.port)
    if self.logger: self.logger.info(f"Server started on {self.host}:{self.port}")

  async def stop(self):
    if self._server:
      self._server.close()
      await self._server.wait_closed()
      self._server = None
      if self.logger: self.logger.info("Server stopped")