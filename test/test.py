import asyncio
import json
import os
import shutil
import sys
from datetime import datetime

# --- Import Logic (Compatible with installed package or local source) ---
try:
    from asynchttpserver.Status import Status
    from asynchttpserver.Method import Method
    from asynchttpserver.Message import RequestMessage, ResponseMessage
    from asynchttpserver.Mime import Mime
    from asynchttpserver import AsyncServer, AsyncRequestRouteHandler
except ImportError:
    # Allow running directly from repo root without installation
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    from asynchttpserver.Status import Status
    from asynchttpserver.Method import Method
    from asynchttpserver.Message import RequestMessage, ResponseMessage
    from asynchttpserver.Mime import Mime
    from asynchttpserver import AsyncServer, AsyncRequestRouteHandler

# --- 1. Custom Logger (Demonstrating Duck Typing / No Logging Dependency) ---
class SimpleColorLogger:
    """A custom logger to prove we don't need the 'logging' module."""
    RESET = "\033[0m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    CYAN = "\033[36m"

    def info(self, msg):
        print(f"{self.GREEN}[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] [INFO]  {msg}{self.RESET}")

    def debug(self, msg):
        print(f"{self.CYAN}[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] [DEBUG] {msg}{self.RESET}")
        pass

    def warning(self, msg):
        print(f"{self.YELLOW}[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] [WARN]  {msg}{self.RESET}")

    def error(self, msg):
        print(f"{self.RED}[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] [ERROR] {msg}{self.RESET}")

# --- 2. Test Content Generation (Static Files) ---
TEST_DIR = "test_site_assets"

def create_test_assets():
    """Generates temporary HTML, CSS, JS, and JSON files for testing."""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(f"{TEST_DIR}/css", exist_ok=True)
    os.makedirs(f"{TEST_DIR}/js", exist_ok=True)
    os.makedirs(f"{TEST_DIR}/data", exist_ok=True)

    # CSS
    with open(f"{TEST_DIR}/css/style.css", "w") as f:
        f.write("""
            body { font-family: sans-serif; background: #f4f4f9; padding: 2rem; }
            .container { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            h1 { color: #333; }
            button { background: #007bff; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 4px;}
            button:hover { background: #0056b3; }
            code { background: #eee; padding: 2px 5px; border-radius: 3px; }
            .response-box { margin-top: 20px; padding: 10px; background: #e9ecef; border-left: 5px solid #007bff; }
        """)

    # JS
    with open(f"{TEST_DIR}/js/app.js", "w") as f:
        f.write("""
            console.log('AsyncHTTPServer Static JS Loaded');
            async function callApi() {
                const res = await fetch('/api/v1/status');
                const data = await res.json();
                document.getElementById('api-response').innerText = JSON.stringify(data, null, 2);
            }
        """)
    
    # Dummy Config (JSON)
    with open(f"{TEST_DIR}/data/config.json", "w") as f:
        f.write('{"server_name": "TestServer", "max_connections": 100}')

def cleanup_test_assets():
    """Removes temporary files."""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

# --- 3. Application Setup ---

logger = SimpleColorLogger()
app = AsyncRequestRouteHandler(logger=logger)

# --> Feature: Static File Serving using the new Mime.py logic
# Mounts ./test_site_assets folder to URL /static
app.static("/static", TEST_DIR)

# --> Feature: Root Page (HTML)
@app.route("/", methods=[Method.GET])
async def home(request: RequestMessage) -> ResponseMessage:
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AsyncHTTPServer Test</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <div class="container">
            <h1>AsyncHTTPServer v2.2 Demo</h1>
            <p>Welcome! This page tests <strong>HTML serving</strong> and <strong>Static Assets</strong> (CSS).</p>
            
            <h3>Interactive Tests:</h3>
            <ul>
                <li><a href="/echo_form">Test POST Request (Form Echo)</a></li>
                <li><a href="/static/data/config.json" target="_blank">View Static JSON File</a></li>
                <li><button onclick="callApi()">Test Async API Fetch</button></li>
            </ul>

            <div id="api-response" class="response-box">API Response will appear here...</div>
        </div>
        <script src="/static/js/app.js"></script>
    </body>
    </html>
    """
    return ResponseMessage(Status.OK, {"Content-Type": Mime.HTML}, html)

# --> Feature: Form Handling (GET to show form, POST to process)
@app.route("/echo_form", methods=[Method.GET, Method.POST])
async def echo_form(request: RequestMessage) -> ResponseMessage:
    if request.method == Method.GET:
        html = """
        <div style="font-family: sans-serif; padding: 2rem;">
            <h2>POST Echo Test</h2>
            <form method="POST" action="/echo_form">
                <label>Name: <input type="text" name="username" value="Developer"></label><br><br>
                <label>Message: <input type="text" name="message" value="Hello World"></label><br><br>
                <button type="submit">Send POST</button>
            </form>
            <br>
            <a href="/">Back to Home</a>
        </div>
        """
        return ResponseMessage(Status.OK, {"Content-Type": Mime.HTML}, html)
    
    elif request.method == Method.POST:
        # Simple body echo
        body_str = request.body.decode('utf-8')
        return ResponseMessage(
            Status.OK, 
            {"Content-Type": Mime.TXT}, 
            f"Received POST Data:\n\n{body_str}".encode('utf-8')
        )

# --> Feature: Sub-Router (API Blueprint)
@app.mount("/api/v1", methods=[Method.GET])
def api_router():
    api = AsyncRequestRouteHandler(logger=logger)

    @api.route("/status", methods=[Method.GET])
    async def status(request: RequestMessage) -> ResponseMessage:
        data = {
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "server": "AsyncHTTPServer/2.2",
            "features": ["async", "static-files", "sub-routing"]
        }
        return ResponseMessage(
            Status.OK,
            {"Content-Type": Mime.JSON},
            json.dumps(data).encode("utf-8")
        )
    
    return api

# --- 4. Server Execution ---

async def main():
    HOST = "0.0.0.0"
    PORT = 8080
    
    create_test_assets()
    
    server = AsyncServer(root_handler=app, host=HOST, port=PORT, logger=logger)
    
    logger.info("=" * 40)
    logger.info(f"Server starting on http://localhost:{PORT}")
    logger.info(f"Static files serving from: {os.path.abspath(TEST_DIR)}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 40)

    try:
        await server.start()
        # Keep the main coroutine alive
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.warning("Stopping server...")
        await server.stop()
        cleanup_test_assets()
        logger.info("Cleaned up temporary assets.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handled in main's finally block usually, but this catches the signal at top level
        pass