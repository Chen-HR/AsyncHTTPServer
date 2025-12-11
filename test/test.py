import asyncio
import logging
import json

try:
  from asynchttpserver.Status import Status
  from asynchttpserver.Method import Method
  from asynchttpserver.Message import RequestMessage, ResponseMessage
  from asynchttpserver import AsyncServer, AsyncRequestRouteHandler, AsyncRequestResponseHandler
except ImportError:
  try:
    from src.asynchttpserver.Status import Status
    from src.asynchttpserver.Method import Method
    from src.asynchttpserver.Message import RequestMessage, ResponseMessage
    from src.asynchttpserver import AsyncServer, AsyncRequestRouteHandler, AsyncRequestResponseHandler
  except ImportError as e:
    print("Error: Could not import asynchttpserver.")
    raise e

# --- Logging Setup ---
logger = logging.getLogger("DecoratorTest")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%H:%M:%S"))
logger.addHandler(handler)

# --- Main Application Setup ---

# 1. Create the main app (router)
app = AsyncRequestRouteHandler(logger=logger)

# 2. Define routes using decorators
@app.route("/", methods=[Method.GET])
async def index(request: RequestMessage) -> ResponseMessage:
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "text/html"},
      body=b"<h1>Test AsyncHTTPServer</h1><ul><li><a href='/hello'>Hello</a></li><li><a href='/api'>API</a><ul><li><a href='/api/version'>Version</a></li><li><a href='/api/echo'>Echo</a></li></ul></li></ul>"
  )

@app.route("/hello", methods=[Method.GET, Method.POST])
async def hello(request: RequestMessage) -> ResponseMessage:
  if request.method == Method.POST:
      name = request.body.decode('utf-8') or "Stranger"
      msg = f"Hello, {name}! (via POST)"
  else:
      msg = "Hello! Send a POST to see more."
      
  return ResponseMessage(
      status=Status.OK,
      header={"Content-Type": "text/plain"},
      body=msg.encode('utf-8')
  )

# 3. Mount a Sub-Router using the @mount decorator
# This pattern allows organizing routes into logical groups (like Flask Blueprints)
@app.mount("/api", methods=[Method.GET, Method.POST])
def register_api_router():
    """
    This function acts as a factory for the sub-router.
    It will be executed immediately, and the returned handler will be mounted.
    """
    logger.info("Mounting API router...")
    
    api = AsyncRequestRouteHandler(logger=logger)

    @api.route("/version", methods=[Method.GET])
    async def api_version(request: RequestMessage) -> ResponseMessage:
      return ResponseMessage(
          status=Status.OK,
          header={"Content-Type": "application/json"},
          body=json.dumps({"version": "2.1"}).encode("utf-8")
      )

    @api.route("/echo", methods=[Method.POST])
    async def api_echo(request: RequestMessage) -> ResponseMessage:
      return ResponseMessage(
          status=Status.OK,
          header={"Content-Type": "application/octet-stream"},
          body=request.body
      )
      
    return api

# --- Server Runner ---

async def main():
  server = AsyncServer(root_handler=app, host='0.0.0.0', port=80, logger=logger)
  
  logger.info("Starting server with decorator-based routing...")
  try:
    await server.start()
    while True:
      await asyncio.sleep(3600)
  except KeyboardInterrupt:
    logger.info("Stopping...")
  finally:
    await server.stop()

if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    pass
  finally:
    logger.info("Shutting down...")
