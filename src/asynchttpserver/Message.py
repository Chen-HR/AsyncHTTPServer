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
