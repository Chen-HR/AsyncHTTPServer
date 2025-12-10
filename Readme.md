# Simple Asynchronous HTTP Server

A lightweight, dependency-free asynchronous HTTP server built using Python's `asyncio` library. This project provides a basic yet extensible foundation for building non-blocking web services and applications.

## Features

- **Fully Asynchronous**: Built on `asyncio` for high-performance, non-blocking I/O.
- **Lightweight & Dependency-Free**: Relies only on Python's standard libraries.
- **Extensible Handler System**: Implement custom logic by extending the `AsyncRequestHandler` abstract base class.
- **Flexible Routing**: A built-in router (`AsyncRequestRouteHandler`) supports path and method-based routing, including nested routers for modular application design.
- **Structured Message Parsing**: Clear separation of `RequestMessage` and `ResponseMessage` for robust HTTP message handling.

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

The following example demonstrates how to set up a server with multiple routes, including a nested router for an `/api` endpoint.

```python
import asyncio
import logging
import json

# Import necessary components from the server library
from src import (
    AsyncServer,
    AsyncRequestResponseHandler,
    AsyncRequestRouteHandler
)
from src.Message import RequestMessage, ResponseMessage
from src.Status import Status
from src.Method import Method

# Setup basic logging
logging.basicConfig(
  format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
  level=logging.INFO,
  datefmt="%Y/%m/%d %H:%M:%S"
)

# --- 1. Define Handler Functions ---

async def handle_root(request: RequestMessage) -> ResponseMessage:
  """Handles requests to the root path."""
  html_content = """
  <html>
    <head><title>Python AsyncHTTP Server</title></head>
    <body>
      <h1>Welcome!</h1>
      <p>This is the root page of the Simple Asynchronous HTTP Server.</p>
      <p><a href="/hello">Say Hello</a></p>
      <p><a href="/api/info">View API Info</a></p>
    </body>
  </html>
  """
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "text/html; charset=utf-8"},
      body=html_content
  )

async def handle_hello(request: RequestMessage) -> ResponseMessage:
  """A simple plain-text endpoint."""
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "text/plain; charset=utf-8"},
      body="Hello from the AsyncHTTP server!"
  )

async def handle_api_info(request: RequestMessage) -> ResponseMessage:
  """A JSON API endpoint."""
  info_body = json.dumps({"service": "api", "version": "1.0", "status": "ok"})
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "application/json"},
      body=info_body
  )

# --- 2. Setup Routing ---

# Create handlers from the functions
root_handler = AsyncRequestResponseHandler(handle_root)
hello_handler = AsyncRequestResponseHandler(handle_hello)
api_info_handler = AsyncRequestResponseHandler(handle_api_info)

# Create a sub-router for the /api path
api_router = AsyncRequestRouteHandler()
api_router.add_route("/info", api_info_handler, method=Method.GET)

# Create the main router and add routes
main_router = AsyncRequestRouteHandler()
main_router.add_route("/", root_handler, method=Method.GET)
main_router.add_route("/hello", hello_handler, method=Method.GET)
main_router.add_route("/api", api_router) # Mount the API sub-router

# --- 3. Main async function to run the server ---
async def main():
  # Initialize the server with the main router on port 8080
  server = AsyncServer(root_handler=main_router, port=8080)

  try:
    await server.start()
    print("Server is running on http://localhost:8080. Press Ctrl+C to stop.")
    # Keep the server running
    await asyncio.Event().wait()
  except KeyboardInterrupt:
    print("\nShutting down server...")
  finally:
    await server.stop()

# --- 4. Run the application ---
if __name__ == "__main__":
  try:
    asyncio.run(main())
  except Exception as e:
    logging.error(f"Failed to run the application: {e}")

```

## License

This project is not licensed. All rights are reserved.
