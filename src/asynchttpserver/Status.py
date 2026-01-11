class Status:
  def __init__(self, code: int, name: str):
    self.code = code
    self.name = name
  def __str__(self) -> str:
    return f"{self.code} {self.name}"
  def __repr__(self) -> str:
    return f"Status({self.code}, {self.name})"
  def __eq__(self, other: "Status") -> bool: # type: ignore
    return self.code == other.code and self.name == other.name
  _map: dict[int, "Status"]
  @classmethod
  def query(cls, code: int) -> "Status":
    if code in cls._map:
      return cls._map[code]
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

Status._map = {status.code: status for status in Status.__dict__.values() if isinstance(status, Status)}
