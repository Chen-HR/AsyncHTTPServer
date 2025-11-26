import asyncio

import logging

try:
  from src.asynchttpserver.Status import Status
  from src.asynchttpserver.Method import Method
  from src.asynchttpserver.Message import RequestMessage, ResponseMessage
  import src.asynchttpserver as AsyncHTTPServer
except ImportError:
  from asynchttpserver.Status import Status # type: ignore
  from asynchttpserver.Method import Method # type: ignore
  from asynchttpserver.Message import RequestMessage, ResponseMessage # type: ignore
  import asynchttpserver as AsyncHTTPServer # type: ignore

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
if __name__ == "__main__":
  try:
    asyncio.run(main())
  except Exception as e:
    pass