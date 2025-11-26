# Project `.`
- Export Time: 2025/11/26 13:21:43

---
## File: `./.gitignore`

```text
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
.venv

```

---
## File: `./.python-version`

```text
3.11

```

---
## File: `./pyproject.toml`

```toml
[project]
name = "asynchttpserver"
version = "1.0.0"
authors = [
  {name = "HRChen", email = "tn918419@gmail.com"},
]
description = "Simple Asynchronous HTTP Server"
readme = "Readme.md"
requires-python = ">=3.11"
classifiers = []
dependencies = [
  "logging>=0.4.9.6",
]

[build-system]
requires = ["uv_build"]
build-backend = "uv_build"

```

---
## File: `./Readme.md`

```markdown

```

---
## File: `./root.md`

```markdown

```

---
## File: `./uv.lock`

```text
version = 1
revision = 1
requires-python = ">=3.11"

[[package]]
name = "asynchttpserver"
version = "0.1.0"
source = { virtual = "." }
dependencies = [
    { name = "logging" },
]

[package.metadata]
requires-dist = [{ name = "logging", specifier = ">=0.4.9.6" }]

[[package]]
name = "logging"
version = "0.4.9.6"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/93/4b/979db9e44be09f71e85c9c8cfc42f258adfb7d93ce01deed2788b2948919/logging-0.4.9.6.tar.gz", hash = "sha256:26f6b50773f085042d301085bd1bf5d9f3735704db9f37c1ce6d8b85c38f2417", size = 96029 }

```

---
## File: `./src/__init__.py`

```python
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

```

---
## File: `./src/Message.py`

```python
import abc

from .Status import Status
from .Method import Method

class Message(abc.ABC):
  def __init__(self, header: dict[str, str], body: str = "", protocol: str = "HTTP/1.1"):
    self.header = header
    self.body = body
    self.protocol = protocol
  @abc.abstractmethod
  def _title(self) -> str:
    pass
  def _header(self) -> str:
    return "\r\n".join([f"{key}: {value}" for key, value in self.header.items()])
  def _body(self) -> str:
    return self.body
  def __str__(self) -> str:
    # Ensure there is a body by adding Content-Length if not present
    if 'Content-Length' not in self.header and self.body:
        self.header['Content-Length'] = str(len(self.body.encode('utf-8')))
    if self.body:
        return "\r\n".join([self._title(), self._header(), "", self._body()])
    else:
        return "\r\n".join([self._title(), self._header(), "\r\n"])
  def pack(self, encoding="utf-8") -> bytes:
    return (self.__str__()).encode(encoding)
  @classmethod
  def unpack(cls, data: bytes, encoding="utf-8") -> "Message": # type: ignore
    pass

class RequestMessage(Message):
  def __init__(self, method: Method, path: str, header: dict[str, str], body: str = "", protocol: str = "HTTP/1.1"):
    super().__init__(header, body, protocol)
    self.method = method
    self.path = path
  def _title(self) -> str:
    return f"{self.method.name} {self.path} {self.protocol}"
  @classmethod
  def unpack(cls, data: bytes, encoding="utf-8") -> "RequestMessage":
    """
    Parses a raw HTTP request from bytes into a RequestMessage object.
    """
    try:
      text = data.decode(encoding)
      parts = text.split('\r\n\r\n', 1)
      header_part = parts[0]
      body = parts[1] if len(parts) > 1 else ""

      header_lines = header_part.split('\r\n')
      request_line = header_lines[0]
      
      method_str, path, protocol = request_line.split(' ', 2)
      method = Method.query(method_str)
      
      headers = {}
      for line in header_lines[1:]:
        if ': ' in line:
          key, value = line.split(': ', 1)
          headers[key] = value
          
      return RequestMessage(method=method, path=path, header=headers, body=body, protocol=protocol)
    except (UnicodeDecodeError, IndexError, ValueError) as e:
      raise ValueError(f"Failed to parse invalid HTTP request: {e}")

class ResponseMessage(Message):
  def __init__(self, status: Status, header: dict[str, str], body: str = "", protocol: str = "HTTP/1.1"):
    super().__init__(header, body, protocol)
    self.status = status
  def _title(self) -> str:
    return f"{self.protocol} {self.status.code} {self.status.name}"
  @classmethod
  def unpack(cls, data: bytes, encoding="utf-8") -> "ResponseMessage":
    """
    Parses a raw HTTP response from bytes into a ResponseMessage object.
    """
    try:
      text = data.decode(encoding)
      parts = text.split('\r\n\r\n', 1)
      header_part = parts[0]
      body = parts[1] if len(parts) > 1 else ""

      header_lines = header_part.split('\r\n')
      status_line = header_lines[0]

      protocol, status_code_str, _ = status_line.split(' ', 2)
      status = Status.query(int(status_code_str))
      
      headers = {}
      for line in header_lines[1:]:
        if ': ' in line:
          key, value = line.split(': ', 1)
          headers[key] = value

      return ResponseMessage(status=status, header=headers, body=body, protocol=protocol)
    except (UnicodeDecodeError, IndexError, ValueError) as e:
      raise ValueError(f"Failed to parse invalid HTTP response: {e}")

```

---
## File: `./src/Method.py`

```python
class Method:
  def __init__(self, name: str):
    self.name = name
  def __str__(self) -> str:
    return f"Method({self.name})"
  def __eq__(self, other: "Method") -> bool: # type: ignore
    return self.name == other.name
  @classmethod
  def query(cls, name: str) -> "Method":
    for Method in cls.__dict__.values():
      if isinstance(Method, cls):
        if Method.name == name:
          return Method
    raise ValueError(f"Unknown Method name: {name}")
  GET    : "Method"
  POST   : "Method"
  PUT    : "Method"
  DELETE : "Method"
  HEAD   : "Method"
  CONNECT: "Method"
  OPTIONS: "Method"
  TRACE  : "Method"
  PATCH  : "Method"

Method.GET    = Method("GET")
Method.POST   = Method("POST")
Method.PUT    = Method("PUT")
Method.DELETE = Method("DELETE")
Method.HEAD   = Method("HEAD")
Method.CONNECT= Method("CONNECT")
Method.OPTIONS= Method("OPTIONS")
Method.TRACE  = Method("TRACE")
Method.PATCH  = Method("PATCH")
```

---
## File: `./src/Status.py`

```python
class Status:
  def __init__(self, code: int, name: str):
    self.code = code
    self.name = name
  def __str__(self) -> str:
    return f"Status({self.code}, {self.name})"
  def __eq__(self, other: "Status") -> bool: # type: ignore
    return self.code == other.code and self.name == other.name
  @classmethod
  def query(cls, code: int) -> "Status":
    for status in cls.__dict__.values():
      if isinstance(status, cls):
        if status.code == code:
          return status
    raise ValueError(f"Unknown status code: {code}")
  # 1xx Informational
  CONTINUE              : "Status"
  SWITCHING_PROTOCOLS   : "Status"
  EARLY_HINTS           : "Status"
  # 2xx Success
  OK                    : "Status"
  CREATED               : "Status"
  ACCEPTED              : "Status"
  NON_AUTHORITATIVE_INFO: "Status"
  NO_CONTENT            : "Status"
  RESET_CONTENT         : "Status"
  PARTIAL_CONTENT       : "Status"
  MULTI_STATUS          : "Status"
  IM_USED               : "Status"
  # 3xx Redirection
  MULTIPLE_CHOICES      : "Status"
  MOVED_PERMANENTLY     : "Status"
  FOUND                 : "Status"
  SEE_OTHER             : "Status"
  NOT_MODIFIED          : "Status"
  TEMPORARY_REDIRECT    : "Status"
  PERMANENT_REDIRECT    : "Status"
  # 4xx Client Error
  BAD_REQUEST                   : "Status"
  UNAUTHORIZED                  : "Status"
  PAYMENT_REQUIRED              : "Status"
  FORBIDDEN                     : "Status"
  NOT_FOUND                     : "Status"
  METHOD_NOT_ALLOWED            : "Status"
  NOT_ACCEPTABLE                : "Status"
  PROXY_AUTHENTICATION_REQUIRED : "Status"
  REQUEST_TIMEOUT               : "Status"
  CONFLICT                      : "Status"
  GONE                          : "Status"
  LENGTH_REQUIRED               : "Status"
  PRECONDITION_FAILED           : "Status"
  PAYLOAD_TOO_LARGE             : "Status"
  URI_TOO_LONG                  : "Status"
  UNSUPPORTED_MEDIA_TYPE        : "Status"
  RANGE_NOT_SATISFIABLE         : "Status"
  EXPECTATION_FAILED            : "Status"
  TOO_MANY_REQUESTS             : "Status"
  HEADER_FIELDS_TOO_LARGE       : "Status"
  UNAVAILABLE_FOR_LEGAL_REASONS : "Status"
  # 5xx Server Error
  INTERNAL_SERVER_ERROR : "Status"
  NOT_IMPLEMENTED       : "Status"
  BAD_GATEWAY           : "Status"
  SERVICE_UNAVAILABLE   : "Status"
  GATEWAY_TIMEOUT       : "Status"
  VERSION_NOT_SUPPORTED : "Status"

# 1xx Informational
Status.CONTINUE            = Status(100, "Continue")
Status.SWITCHING_PROTOCOLS = Status(101, "Switching Protocols")
Status.EARLY_HINTS         = Status(103, "Early Hints")
# 2xx Success
Status.OK                     = Status(200, "OK")
Status.CREATED                = Status(201, "Created")
Status.ACCEPTED               = Status(202, "Accepted")
Status.NON_AUTHORITATIVE_INFO = Status(203, "Non-Authoritative Information")
Status.NO_CONTENT             = Status(204, "No Content")
Status.RESET_CONTENT          = Status(205, "Reset Content")
Status.PARTIAL_CONTENT        = Status(206, "Partial Content")
Status.MULTI_STATUS           = Status(207, "Multi-Status")
Status.IM_USED                = Status(226, "IM Used")
# 3xx Redirection
Status.MULTIPLE_CHOICES   = Status(300, "Multiple Choices")
Status.MOVED_PERMANENTLY  = Status(301, "Moved Permanently")
Status.FOUND              = Status(302, "Found")
Status.SEE_OTHER          = Status(303, "See Other")
Status.NOT_MODIFIED       = Status(304, "Not Modified")
Status.TEMPORARY_REDIRECT = Status(307, "Temporary Redirect")
Status.PERMANENT_REDIRECT = Status(308, "Permanent Redirect")
# 4xx Client Error
Status.BAD_REQUEST                   = Status(400, "Bad Request")
Status.UNAUTHORIZED                  = Status(401, "Unauthorized")
Status.PAYMENT_REQUIRED              = Status(402, "Payment Required")
Status.FORBIDDEN                     = Status(403, "Forbidden")
Status.NOT_FOUND                     = Status(404, "Not Found")
Status.METHOD_NOT_ALLOWED            = Status(405, "Method Not Allowed")
Status.NOT_ACCEPTABLE                = Status(406, "Not Acceptable")
Status.PROXY_AUTHENTICATION_REQUIRED = Status(407, "Proxy Authentication Required")
Status.REQUEST_TIMEOUT               = Status(408, "Request Timeout")
Status.CONFLICT                      = Status(409, "Conflict")
Status.GONE                          = Status(410, "Gone")
Status.LENGTH_REQUIRED               = Status(411, "Length Required")
Status.PRECONDITION_FAILED           = Status(412, "Precondition Failed")
Status.PAYLOAD_TOO_LARGE             = Status(413, "Payload Too Large")
Status.URI_TOO_LONG                  = Status(414, "URI Too Long")
Status.UNSUPPORTED_MEDIA_TYPE        = Status(415, "Unsupported Media Type")
Status.RANGE_NOT_SATISFIABLE         = Status(416, "Range Not Satisfiable")
Status.EXPECTATION_FAILED            = Status(417, "Expectation Failed")
Status.TOO_MANY_REQUESTS             = Status(429, "Too Many Requests")
Status.HEADER_FIELDS_TOO_LARGE       = Status(431, "Request Header Fields Too Large")
Status.UNAVAILABLE_FOR_LEGAL_REASONS = Status(451, "Unavailable For Legal Reasons")
# 5xx Server Error
Status.INTERNAL_SERVER_ERROR = Status(500, "Internal Server Error")
Status.NOT_IMPLEMENTED       = Status(501, "Not Implemented")
Status.BAD_GATEWAY           = Status(502, "Bad Gateway")
Status.SERVICE_UNAVAILABLE   = Status(503, "Service Unavailable")
Status.GATEWAY_TIMEOUT       = Status(504, "Gateway Timeout")
Status.VERSION_NOT_SUPPORTED = Status(505, "HTTP Version Not Supported")

```

---
## File: `./test/test.py`

```python
import asyncio

import logging

from src.Status import Status
from src.Method import Method
from src.Message import RequestMessage, ResponseMessage
import src as AsyncHTTPServer

# Setup logging
logging.basicConfig(
  format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
  level=logging.INFO,
  datefmt="%Y/%m/%d %H:%M:%S"
)

# --- 1. Define Handler Functions ---
async def handle_root(request: RequestMessage) -> ResponseMessage:
  html_content = """
  <html>
    <head><title>Python AsyncHTTP Server</title></head>
    <body>
      <h1>Welcome!</h1>
      <p>This is the root page.</p>
      <p><a href="/hello">Say Hello</a></p>
      <p><a href="/api/info">View API Info</a></p>
    </body>
  </html>
  """
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "text/html"},
      body=html_content
  )
  
async def handle_hello(request: RequestMessage) -> ResponseMessage:
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "text/plain"},
      body="Hello from the AsyncHTTP server!"
  )
  
async def handle_api_info(request: RequestMessage) -> ResponseMessage:
  import json
  info_body = json.dumps({"service": "api", "version": "1.0"})
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "application/json"},
      body=info_body
  )

# --- 2. Setup Routing ---

# Create handlers for specific responses
root_handler = AsyncHTTPServer.AsyncRequestResponseHandler(handle_root)
hello_handler = AsyncHTTPServer.AsyncRequestResponseHandler(handle_hello)
api_info_handler = AsyncHTTPServer.AsyncRequestResponseHandler(handle_api_info)

# Create a sub-router for the /api path
api_router = AsyncHTTPServer.AsyncRequestRouteHandler()
api_router.add_route("/info", api_info_handler, method=Method.GET)

# Create the main router
main_router = AsyncHTTPServer.AsyncRequestRouteHandler()
main_router.add_route("/", root_handler, method=Method.GET)
main_router.add_route("/hello", hello_handler, method=Method.GET)
main_router.add_route("/api", api_router) # Nest the API router

# --- 3. Main async function ---
async def main():
  
  # --- Server Initialization ---
  server = AsyncHTTPServer.AsyncServer(root_handler=main_router, port=80)
  
  try:
    await server.start()
    # Keep the server running indefinitely
    while True:
      await asyncio.sleep(10)
  except KeyboardInterrupt:
    pass
  finally:
    await server.stop()

# --- 4. Run the application ---
try:
  asyncio.run(main())
except Exception as e:
  pass
```

---

