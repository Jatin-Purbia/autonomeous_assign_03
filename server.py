"""Launch Argument Lab. Runtime uses only Python's standard library."""

import argparse
import logging
from argumentation.webapp import create_server

__all__ = ["create_server", "main"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--verbose", action="store_true", help="Log HTTP requests and diagnostics.")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        server = create_server(args.port)
    except (OSError, OverflowError) as exc:
        parser.exit(1, f"Cannot start Argument Lab on port {args.port}: {exc}\n")
    print(f"Argument Lab is running at http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
