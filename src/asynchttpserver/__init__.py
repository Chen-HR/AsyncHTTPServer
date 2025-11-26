import abc
import asyncio
import logging

from .Status import Status
from .Method import Method
from .Message import RequestMessage, ResponseMessage

class AsyncRequestHandler(abc.ABC):
  """Abstract base class for handling asynchronous HTTP requests."""
  @abc.abstractmethod
  async def handle(self, request: RequestMessage) -> ResponseMessage:
    """
    Processes an incoming RequestMessage and returns a ResponseMessage.

    Args:
      request (RequestMessage): The incoming HTTP request.

    Returns:
      ResponseMessage: The HTTP response to be sent to the client.
    """
    pass

class AsyncRequestResponseHandler(AsyncRequestHandler):
  """A concrete request handler that uses a callback to generate a response."""
  def __init__(self, callback):
    """
    Initializes the handler with a user-defined callback function.

    Args:
      callback (callable): An async function that takes a RequestMessage and returns a ResponseMessage.
    """
    # if not inspect.iscoroutinefunction(callback):
    #   raise TypeError("Callback must be an async function.")
    self._callback = callback

  async def handle(self, request: RequestMessage) -> ResponseMessage:
    return await self._callback(request)

class AsyncRequestRouteHandler(AsyncRequestHandler):
  """
  A request handler that routes requests to other handlers based on path and method.
  Supports nested routing through path prefix matching.
  """
  def __init__(self):
    # { "GET": {"/path": handler}, "POST": {"/path2": handler} }
    self._routes: dict[str, dict[str, AsyncRequestHandler]] = {}

  def add_route(self, path: str, handler: AsyncRequestHandler, method: Method = Method.GET):
    """
    Adds a route to the routing table.

    Args:
      path (str): The URL path prefix to match.
      handler (AsyncRequestHandler): The handler to process requests for this route.
      method (Method, optional): The HTTP method for this route. Defaults to Method.GET.
    """
    method_name = method.name
    if method_name not in self._routes:
      self._routes[method_name] = {}
    self._routes[method_name][path] = handler

  async def handle(self, request: RequestMessage) -> ResponseMessage:
    method_routes = self._routes.get(request.method.name, {})
    
    # Find the longest matching path prefix
    best_match_path = ""
    handler = None
    for path, registered_handler in method_routes.items():
      if request.path.startswith(path):
        if len(path) > len(best_match_path):
          best_match_path = path
          handler = registered_handler
          
    if handler:
      logging.debug(f"Routing {request.method} {request.path} to {handler}")
      modified_request = RequestMessage(
        method=request.method,
        path=request.path[len(best_match_path):],
        header=request.header,
        body=request.body,
        protocol=request.protocol
      )
      return await handler.handle(modified_request)
    else:
      logging.debug(f"No route found for {request.method} {request.path}")
      return ResponseMessage(
        status=Status.NOT_FOUND,
        header={"Content-Type": "text/plain", "Connection": "close"},
        body=f"404 Not Found: {request.path}"
      )

class AsyncServer:
  """An asynchronous HTTP server that listens for and handles connections."""
  def __init__(self, root_handler: AsyncRequestHandler, host: str = '0.0.0.0', port: int = 80):
    """
    Initializes the asynchronous HTTP server.

    Args:
      root_handler (AsyncRequestHandler): The root handler to process all incoming requests.
      host (str, optional): The host address to bind to. Defaults to '0.0.0.0'.
      port (int, optional): The port to listen on. Defaults to 80.
      log_level (Logging.Level, optional): Logging level. Defaults to Logging.LEVEL.INFO.
    """
    self.root_handler = root_handler
    self.host = host
    self.port = port
    self._server = None

  async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try: 
      host, port = writer.get_extra_info('peername')
      logging.info(f"New connection from {host}:{port}")
    except Exception as e:
      pass
    try:
      # Read the request line and headers
      raw_request = await reader.read(1024)
      if not raw_request:
        writer.close()
        await writer.wait_closed()
        return

      request = RequestMessage.unpack(raw_request)
      
      response = await self.root_handler.handle(request)
      
      writer.write(response.pack())
      await writer.drain()
    except ValueError as e:
      logging.error(f"Invalid HTTP request: {e}")
      response = ResponseMessage(
        status=Status.BAD_REQUEST,
        header={"Content-Type": "text/plain", "Connection": "close"},
        body="400 Bad Request"
      )
      writer.write(response.pack())
      await writer.drain()
    except Exception as e:
      logging.error(f"Internal server error: {e}")
      response = ResponseMessage(
        status=Status.INTERNAL_SERVER_ERROR,
        header={"Content-Type": "text/plain", "Connection": "close"},
        body="500 Internal Server Error"
      )
      writer.write(response.pack())
      await writer.drain()
    finally:
      writer.close()
      await writer.wait_closed()

  async def start(self):
    """Starts the asyncio server."""
    if self._server:
      return
    self._server = await asyncio.start_server(self._handle_connection, self.host, self.port)
    logging.info(f"Server started on {self.host}:{self.port}")

  async def stop(self):
    """Stops the asyncio server."""
    if self._server:
      self._server.close()
      await self._server.wait_closed()
      self._server = None
      logging.info("Server stopped")
