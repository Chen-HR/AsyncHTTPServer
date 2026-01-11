import os

class Mime:
  """
  Helper class for MIME type definitions and resolving.
  Provides common constants and file extension mapping.
  """
  
  # Common MIME Types Constants
  HTML = "text/html"
  CSS  = "text/css"
  JS   = "application/javascript"
  JSON = "application/json"
  PNG  = "image/png"
  JPG  = "image/jpeg"
  GIF  = "image/gif"
  SVG  = "image/svg+xml"
  ICO  = "image/x-icon"
  TXT  = "text/plain"
  XML  = "text/xml"
  PDF  = "application/pdf"
  ZIP  = "application/zip"
  BIN  = "application/octet-stream"

  # Extension Mapping
  _map = {
      ".html": HTML,
      ".htm":  HTML,
      ".css":  CSS,
      ".js":   JS,
      ".mjs":  JS,
      ".json": JSON,
      ".png":  PNG,
      ".jpg":  JPG,
      ".jpeg": JPG,
      ".gif":  GIF,
      ".svg":  SVG,
      ".ico":  ICO,
      ".txt":  TXT,
      ".xml":  XML,
      ".pdf":  PDF,
      ".zip":  ZIP,
  }

  @classmethod
  def guess_type(cls, path: str) -> str:
    """
    Guess the MIME type based on the file extension.
    Returns application/octet-stream if unknown.
    """
    try:
        _, ext = os.path.splitext(path)
        return cls._map.get(ext.lower(), cls.BIN)
    except Exception:
        return cls.BIN