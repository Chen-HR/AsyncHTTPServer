import abc

try:
  from .Status import Status
  from .Method import Method
except ImportError:
  from asynchttpserver.Status import Status
  from asynchttpserver.Method import Method

class Message(abc.ABC):
  def __init__(self, header: dict[str, str], body: bytes = b"", version: str = "1.1"):
    """
    Initializes a Message object.

    Args:
      header (dict[str, str]): HTTP headers. Keys will be normalized to lowercase.
      body (bytes, optional): The message body. Defaults to b"".
      version (str, optional): HTTP protocol version (e.g., "1.1"). Defaults to "1.1".
    """
    # Normalize header keys to lowercase
    self.header = {k.lower(): v for k, v in header.items()}
    
    # Ensure body is bytes (Auto-encode if str is passed by accident, though type hint says bytes)
    if isinstance(body, str):
      self.body = body.encode("utf-8")
    else:
      self.body = body
      
    self.version = version

  @property
  def protocol(self) -> str:
    """Helper to reconstruct the protocol string."""
    return f"HTTP/{self.version}"

  @abc.abstractmethod
  def _title(self) -> str:
    pass

  def _header(self) -> str:
    # Output headers. 
    # Note: Keys are stored in lowercase. 
    return "\r\n".join([f"{key}: {value}" for key, value in self.header.items()])

  def pack(self) -> bytes:
    """
    Packs the message into bytes for transmission.
    """
    # Auto-calculate Content-Length
    self.header['content-length'] = str(len(self.body))
    
    title_line = self._title()
    header_block = self._header()
    
    # Assemble: Title + Headers + Empty Line + Body
    # Encode headers as UTF-8 (ASCII compatible)
    head_bytes = f"{title_line}\r\n{header_block}\r\n\r\n".encode("utf-8")
    
    return head_bytes + self.body

  @classmethod
  def unpack(cls, data: bytes) -> "Message": # type: ignore
    raise NotImplementedError("Use specific unpack methods in subclasses")

class RequestMessage(Message):
  def __init__(self, method: Method, path: str, header: dict[str, str], body: bytes = b"", version: str = "1.1"):
    super().__init__(header, body, version)
    self.method = method
    self.path = path

  def _title(self) -> str:
    return f"{self.method.name} {self.path} {self.protocol}"

  @classmethod
  def unpack_header(cls, header_data: bytes) -> "RequestMessage":
    """
    Parses ONLY the HTTP header section from bytes.
    """
    try:
      text = header_data.decode("utf-8")
      lines = text.split('\r\n')
      
      request_line = lines[0]
      if not request_line:
         raise ValueError("Empty request line")

      # Format: GET /path HTTP/1.1
      parts = request_line.split(' ')
      if len(parts) != 3:
          raise ValueError("Malformed request line")
      
      method_str, path, protocol_str = parts
      method = Method.query(method_str)
      
      # Extract version from "HTTP/1.1" -> "1.1"
      version = "1.1"
      if '/' in protocol_str:
          version = protocol_str.split('/', 1)[1]
      
      headers = {}
      for line in lines[1:]:
        if not line: continue
        if ': ' in line:
          key, value = line.split(': ', 1)
          headers[key] = value
        elif ':' in line:
          key, value = line.split(':', 1)
          headers[key] = value

      return RequestMessage(method=method, path=path, header=headers, body=b"", version=version)
      
    except (UnicodeDecodeError, IndexError, ValueError) as e:
      raise ValueError(f"Failed to parse HTTP request headers: {e}")

class ResponseMessage(Message):
  def __init__(self, status: Status, header: dict[str, str], body: bytes = b"", version: str = "1.1"):
    super().__init__(header, body, version)
    self.status = status

  def _title(self) -> str:
    return f"{self.protocol} {self.status.code} {self.status.name}"

  @classmethod
  def unpack(cls, data: bytes) -> "ResponseMessage":
    """
    Parses a complete raw HTTP response.
    """
    try:
      parts = data.split(b'\r\n\r\n', 1)
      header_bytes = parts[0]
      body_bytes = parts[1] if len(parts) > 1 else b""
      
      text = header_bytes.decode("utf-8")
      header_lines = text.split('\r\n')
      
      status_line = header_lines[0]
      if not status_line:
         raise ValueError("Empty status line")

      # Format: HTTP/1.1 200 OK
      line_parts = status_line.split(' ', 2)
      if len(line_parts) < 2:
          raise ValueError("Malformed status line")
          
      protocol_str = line_parts[0]
      status_code_str = line_parts[1]
      
      # Extract version
      version = "1.1"
      if '/' in protocol_str:
          version = protocol_str.split('/', 1)[1]
          
      status = Status.query(int(status_code_str))
      
      headers = {}
      for line in header_lines[1:]:
        if not line: continue
        if ': ' in line:
          key, value = line.split(': ', 1)
          headers[key] = value
        elif ':' in line:
          key, value = line.split(':', 1)
          headers[key] = value

      return ResponseMessage(status=status, header=headers, body=body_bytes, version=version)
    except (UnicodeDecodeError, IndexError, ValueError) as e:
      raise ValueError(f"Failed to parse HTTP response: {e}")