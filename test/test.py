import asyncio
import logging
import json

# --- Imports with fallback for different directory structures ---
try:
  # Try importing from the local library directory structure
  from asynchttpserver.Status import Status
  from asynchttpserver.Method import Method
  from asynchttpserver.Message import RequestMessage, ResponseMessage
  from asynchttpserver import AsyncServer, AsyncRequestResponseHandler, AsyncRequestRouteHandler
except ImportError:
  try:
    # Try importing with src prefix (common in some IDEs)
    from src.asynchttpserver.Status import Status
    from src.asynchttpserver.Method import Method
    from src.asynchttpserver.Message import RequestMessage, ResponseMessage
    from src.asynchttpserver import AsyncServer, AsyncRequestResponseHandler, AsyncRequestRouteHandler
  except ImportError as e:
    print("Error: Could not import asynchttpserver. Make sure the library is in the python path.")
    raise e

# --- Logging Setup ---
# Create a logger with a stream handler to output to console
logger = logging.getLogger("AsyncHTTPServer_Test")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s", "%Y/%m/%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

# --- 1. Define Handler Functions ---

async def handle_root(request: RequestMessage) -> ResponseMessage:
  """
  Handles requests to the root path '/'.
  Returns a simple HTML page.
  """
  html_content = """
  <html>
    <head><title>Python AsyncHTTP Server</title></head>
    <body>
      <h1>Welcome!</h1>
      <p>This is the root page.</p>
      <ul>
        <li><a href="/hello">Say Hello (Plain Text)</a></li>
        <li><a href="/api/info">API Info (JSON)</a></li>
      </ul>
      <p><i>Server is running asynchronously.</i></p>
    </body>
  </html>
  """
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "text/html"},
      body=html_content.encode("utf-8") # String will be auto-encoded to utf-8 bytes
  )

async def handle_hello(request: RequestMessage) -> ResponseMessage:
  """
  Handles requests to '/hello'.
  Returns a plain text response.
  """
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "text/plain"},
      body=b"Hello from the AsyncHTTP server!"
  )

async def handle_api_info(request: RequestMessage) -> ResponseMessage:
  """
  Handles requests to '/api/info'.
  Returns a JSON response.
  """
  info_data = {
    "service": "AsyncHTTPServer API", 
    "version": "2.0",
    "status": "running"
  }
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "application/json"},
      body=json.dumps(info_data).encode("utf-8")
  )

# --- 2. Setup Routing ---

async def setup_routes() -> AsyncRequestRouteHandler:
  # 1. Create concrete handlers for specific endpoints
  # These handlers wrap the async functions defined above
  root_handler = AsyncRequestResponseHandler(handle_root)
  hello_handler = AsyncRequestResponseHandler(handle_hello)
  api_info_handler = AsyncRequestResponseHandler(handle_api_info)

  # 2. Create a sub-router for the '/api' path
  # Requests starting with /api will be forwarded here. 
  # E.g., '/api/info' becomes '/info' when reaching this router.
  api_router = AsyncRequestRouteHandler(logger=logger)
  api_router.add_route("/info", api_info_handler, method=Method.GET)

  # 3. Create the main (root) router
  main_router = AsyncRequestRouteHandler(logger=logger)
  
  # Register routes
  main_router.add_route("/", root_handler, method=Method.GET)
  main_router.add_route("/hello", hello_handler, method=Method.GET)
  
  # Register the sub-router
  # Note: Since we only register it for Method.GET, only GET requests to /api... will work.
  # To support POST /api..., you would need to add_route("/api", api_router, method=Method.POST) as well.
  main_router.add_route("/api", api_router, method=Method.GET)
  
  return main_router

# --- 3. Main async function ---

async def main():
  # Setup the router
  router = await setup_routes()
  
  # Initialize the server
  # Port 80 usually requires administrative privileges (sudo) on Linux/macOS. 
  # Use a higher port like 8080 for development if needed.
  PORT = 80 
  HOST = '0.0.0.0'
  
  server = AsyncServer(root_handler=router, host=HOST, port=PORT, logger=logger)
  
  logger.info(f"Initializing server on {HOST}:{PORT}...")
  
  try:
    await server.start()
    logger.info("Server is up and running. Press Ctrl+C to stop.")
    
    # Keep the main coroutine alive
    # In a real application, you might use an asyncio.Event() to wait for a shutdown signal
    while True:
      await asyncio.sleep(3600) # Sleep for an hour, wake up occasionally
      
  except asyncio.CancelledError:
    logger.info("Main task cancelled.")
  except KeyboardInterrupt:
    logger.info("Received KeyboardInterrupt.")
  except Exception as e:
    logger.error(f"Unexpected error: {e}")
  finally:
    logger.info("Stopping server...")
    await server.stop()
    logger.info("Server stopped.")

# --- 4. Run the application ---

if __name__ == "__main__":
  try:
    # Use asyncio.run() to manage the event loop lifecycle
    asyncio.run(main())
  except KeyboardInterrupt:
    # Handle Ctrl+C gracefully if it bubbles up past asyncio.run
    pass