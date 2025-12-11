# Simple Asynchronous HTTP Server

A lightweight, dependency-free asynchronous HTTP server built using Python's `asyncio` library. This project provides a basic yet extensible foundation for building non-blocking web services and applications.

## Features

- **Fully Asynchronous**: Built on `asyncio` for high-performance, non-blocking I/O.
- **Flask-style Decorators**: Register routes easily using `@app.route` and `@app.mount` decorators.
- **Lightweight & Dependency-Free**: Relies only on Python's standard libraries.
- **Flexible Routing**: Supports method-based routing (`GET`, `POST`, etc.) and nested sub-routers (Blueprints pattern).
- **Binary Data Support**: Optimized `RequestMessage` handling with `bytes` body for file uploads and binary payloads.
- **Memory Safety**: Configurable limits for header and body sizes to prevent OOM on microcontrollers.

## Installation

### (Optional) Create a Virtual Environment

```bash
uv venv .venv
```

### Clone the repository

```bash
git clone https://github.com/Chen-HR/AsyncHTTPServer.git
```

### Install

```bash
uv pip install ./AsyncHTTPServer
```

### (Optional) Remove the repository

```bash
rm -rf AsyncHTTPServer
```

## Usage

The following example demonstrates how to set up a server using the new decorator syntax, including handling POST data and mounting a sub-router for an `/api` endpoint.

```python
import asyncio
import logging
import json

# Import necessary components
from asynchttpserver import AsyncServer, AsyncRequestRouteHandler
from asynchttpserver.Message import RequestMessage, ResponseMessage
from asynchttpserver.Status import Status
from asynchttpserver.Method import Method

# Setup basic logging
logging.basicConfig(
  format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
  level=logging.INFO,
  datefmt="%Y/%m/%d %H:%M:%S"
)
logger = logging.getLogger("App")

# --- 1. Initialize the Main Router ---
app = AsyncRequestRouteHandler(logger=logger)

# --- 2. Define Routes using Decorators ---

@app.route("/", methods=[Method.GET])
async def handle_root(request: RequestMessage) -> ResponseMessage:
  """Handles requests to the root path."""
  html_content = """
  <html>
    <head><title>Python AsyncHTTP Server</title></head>
    <body>
      <h1>Welcome!</h1>
      <p>This is the root page.</p>
      <ul>
        <li><a href="/hello">Say Hello</a></li>
        <li><a href="/api/info">View API Info</a></li>
      </ul>
    </body>
  </html>
  """
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "text/html; charset=utf-8"},
      body=html_content # Auto-encoded to UTF-8 bytes
  )

@app.route("/hello", methods=[Method.GET, Method.POST])
async def handle_hello(request: RequestMessage) -> ResponseMessage:
  """Handles both GET and POST requests."""
  if request.method == Method.POST:
      # Body is bytes, so decode it
      name = request.body.decode('utf-8') or "Stranger"
      msg = f"Hello, {name}! (Received via POST)"
  else:
      msg = "Hello! Send a POST request with your name to see more."

  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "text/plain; charset=utf-8"},
      body=msg
  )

# --- 3. Mount a Sub-Router (Nested Routing) ---

@app.mount("/api", methods=[Method.GET])
def api_router_factory():
    """
    Creates and configures a sub-router. 
    Routes defined here will be prefixed with /api (e.g., /api/info).
    """
    api = AsyncRequestRouteHandler(logger=logger)
    
    @api.route("/info", methods=[Method.GET])
    async def api_info(request: RequestMessage) -> ResponseMessage:
        data = {"service": "AsyncHTTPServer", "version": "2.0", "status": "active"}
        return ResponseMessage(
            status=Status.OK,
            header={"Content-Type": "application/json"},
            body=json.dumps(data)
        )
    
    return api

# --- 4. Main async function to run the server ---
async def main():
  # Initialize the server with the main router on port 8080
  server = AsyncServer(root_handler=app, port=8080, logger=logger)

  try:
    await server.start()
    print("Server is running on http://localhost:8080. Press Ctrl+C to stop.")
    # Keep the server running
    while True:
        await asyncio.sleep(3600)
  except KeyboardInterrupt:
    print("\nShutting down server...")
  finally:
    await server.stop()

# --- 5. Run the application ---
if __name__ == "__main__":
  try:
    asyncio.run(main())
  except Exception as e:
    logging.error(f"Failed to run the application: {e}")
```
