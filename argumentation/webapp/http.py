"""HTTP transport for the local college-project application."""

import json
import logging
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from argumentation.examples import EXAMPLES
from .jobs import ExperimentJobs
from .services import analyse, strategic
from .validation import ExperimentRequest, JsonObject

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_REQUEST_BYTES = 100_000
STATIC_ROUTES = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}


class ApplicationServer(ThreadingHTTPServer):
    """Each server owns its job manager and resource root; no module-global jobs."""

    def __init__(self, port: int, root: Path, jobs: ExperimentJobs):
        self.root = root
        self.jobs = jobs
        super().__init__(("127.0.0.1", port), Handler)


class Handler(BaseHTTPRequestHandler):
    server: ApplicationServer
    server_version = "ArgumentLab/1.0"
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, message: str, *args: object) -> None:
        LOGGER.info("%s %r", self.client_address[0], message % args)

    def send_json(self, data: JsonObject, status: int = 200) -> None:
        self._send(json.dumps(data).encode("utf-8"), "application/json; charset=utf-8", status)

    def _send(self, payload: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            LOGGER.debug("Client disconnected before response completed")

    def do_GET(self) -> None:
        try:
            self._get(urlparse(self.path).path)
        except (OSError, ValueError):
            LOGGER.exception("Failed to serve %r", self.path)
            self.send_json(
                {"error": "Unable to read application resources. Check the server log."}, 500
            )

    def _get(self, path: str) -> None:
        if path == "/api/health":
            return self.send_json(
                {"status": "ok", "application": "Argument Lab", "version": "1.0.0"}
            )
        if path == "/api/examples":
            return self.send_json(EXAMPLES)
        if path == "/api/saved-experiments":
            target = self.server.root / "results" / "experiments.json"
            result = (
                json.loads(target.read_text(encoding="utf-8"))
                if target.exists()
                else {"summary": [], "records": []}
            )
            return self.send_json(result)
        if path.startswith("/api/jobs/"):
            job = self.server.jobs.get(path.rsplit("/", 1)[-1])
            return self.send_json(
                job or {"error": "Job not found."}, 200 if job is not None else 404
            )
        if path not in STATIC_ROUTES:
            return self.send_json({"error": "Not found."}, 404)
        file = self.server.root / "web" / STATIC_ROUTES[path]
        content_type = mimetypes.guess_type(str(file))[0] or "text/plain"
        self._send(file.read_bytes(), content_type + "; charset=utf-8")

    def do_POST(self) -> None:
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + self.headers.get("Host", ""):
            return self.send_json({"error": "Cross-origin request denied."}, 403)
        routes = {"/api/analyse": analyse, "/api/strategic": strategic}
        if self.path not in (*routes, "/api/experiments"):
            return self.send_json({"error": "Not found."}, 404)
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 < length <= MAX_REQUEST_BYTES:
                raise ValueError(f"Request must be 1-{MAX_REQUEST_BYTES} bytes.")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Use application/json.")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object.")
            if self.path == "/api/experiments":
                result = self.server.jobs.start(ExperimentRequest.from_json(data))
            else:
                result = routes[self.path](data)
        except (ValueError, TypeError, KeyError) as exc:
            return self.send_json({"error": str(exc)}, 400)
        except Exception:
            LOGGER.exception("Unhandled error while serving %r", self.path)
            return self.send_json(
                {"error": "Unexpected application error. Check the server log."}, 500
            )
        self.send_json(result)


def create_server(
    port: int = 8000,
    *,
    root: Path | None = None,
    jobs: ExperimentJobs | None = None,
) -> ApplicationServer:
    """Create an unstarted loopback server; port 0 selects a free port for tests."""
    return ApplicationServer(port, root or PROJECT_ROOT, jobs or ExperimentJobs())
