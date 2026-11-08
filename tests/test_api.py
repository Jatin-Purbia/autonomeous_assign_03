import json
import threading
import time
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from server import create_server
from argumentation.examples import EXAMPLES


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request(self, path, data=None, headers=None):
        request = Request(
            self.base + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        with urlopen(request, timeout=15) as response:
            return json.load(response)

    def test_static_and_404(self):
        for path in ["/", "/app.js", "/style.css"]:
            with urlopen(self.base + path) as response:
                self.assertEqual(response.status, 200)
        with self.assertRaises(HTTPError) as error:
            self.request("/../../server.py")
        self.assertEqual(error.exception.code, 404)

    def test_semantics_route(self):
        result = self.request("/api/analyse", EXAMPLES["book-5.2"])
        self.assertEqual(len(result["extensions"]["complete"]), 3)
        self.assertEqual(result["extensions"]["grounded"], [["a3"]])

    def test_strategic_route(self):
        result = self.request("/api/strategic", EXAMPLES["book-5.10"])
        self.assertEqual(result["utilities"], {"x": 1, "y": 0, "z": 1})
        self.assertFalse(result["strategyproofness"]["strategyproof"])

    def test_validation_returns_400(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/api/analyse", {"arguments": ["a"], "attacks": [["a", "missing"]]})
        self.assertEqual(error.exception.code, 400)
        self.assertIn("Unknown", json.load(error.exception)["error"])

    def test_cross_origin_rejected(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/api/analyse", EXAMPLES["chain"], {"Origin": "https://example.org"})
        self.assertEqual(error.exception.code, 403)

    def test_experiment_job(self):
        job = self.request("/api/experiments", {"count": 2, "probabilities": [0.1], "seed": 3})
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            result = self.request("/api/jobs/" + job["job_id"])
            if result["status"] != "running":
                break
            time.sleep(0.02)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(result["result"]["records"]), 2)

    def test_experiment_bad_config(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/api/experiments", {"count": 0})
        self.assertEqual(error.exception.code, 400)

    def test_health_and_response_headers(self):
        self.assertEqual(self.request("/api/health")["status"], "ok")
        with urlopen(self.base + "/") as response:
            self.assertIn("charset=utf-8", response.headers["Content-Type"])
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")

    def test_malformed_json_and_content_type(self):
        for payload, content_type in [(b"{bad", "application/json"), (b"{}", "text/plain")]:
            with self.subTest(content_type=content_type, payload=payload):
                req = Request(
                    self.base + "/api/analyse", data=payload, headers={"Content-Type": content_type}
                )
                with self.assertRaises(HTTPError) as error:
                    urlopen(req, timeout=5)
                self.assertEqual(error.exception.code, 400)
                self.assertIn("error", json.load(error.exception))

    def test_wrong_json_shapes_return_400_without_dropping_connection(self):
        for field, value in [
            ("arguments", "abc"),
            ("attacks", {}),
            ("set", "a"),
            ("attacks", [[{}, "a"]]),
        ]:
            with self.subTest(field=field, value=value):
                with self.assertRaises(HTTPError) as error:
                    self.request("/api/analyse", {**EXAMPLES["chain"], field: value})
                self.assertEqual(error.exception.code, 400)
                self.assertIn("error", json.load(error.exception))
        for field, value in [
            ("ownership", []),
            ("reports", []),
            ("agent", []),
            ("reports", {"x": "a"}),
        ]:
            with self.subTest(field=field, value=value):
                with self.assertRaises(HTTPError) as error:
                    self.request("/api/strategic", {**EXAMPLES["book-5.10"], field: value})
                self.assertEqual(error.exception.code, 400)
        self.assertEqual(self.request("/api/health")["status"], "ok")

    def test_payload_limit_and_unknown_routes(self):
        req = Request(
            self.base + "/api/analyse",
            data=b" " * 100001,
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as error:
            urlopen(req, timeout=5)
        self.assertEqual(error.exception.code, 400)
        for path in ["/api/jobs/unknown", "/api/not-a-route"]:
            with self.assertRaises(HTTPError) as error:
                self.request(path)
            self.assertEqual(error.exception.code, 404)

    def test_explicit_false_boolean_is_not_coerced_from_a_string(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/api/experiments", {"count": 1, "self_attacks": "false"})
        self.assertEqual(error.exception.code, 400)
        self.assertIn("true or false", json.load(error.exception)["error"])


if __name__ == "__main__":
    unittest.main()
