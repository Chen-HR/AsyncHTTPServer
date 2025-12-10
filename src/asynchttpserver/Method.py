class Method:
  def __init__(self, name: str):
    self.name = name
  def __str__(self) -> str:
    return f"Method({self.name})"
  def __eq__(self, other: "Method") -> bool: # type: ignore
    return self.name == other.name
  _map: dict[str, "Method"]
  @classmethod
  def query(cls, name: str) -> "Method":
    if name in cls._map:
      return cls._map[name]
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

Method._map = {method.name: method for method in Method.__dict__.values() if isinstance(method, Method)}
