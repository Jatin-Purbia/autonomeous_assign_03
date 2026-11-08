"""Run unittest and persist a portable verification summary."""

import io
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
suite = unittest.defaultTestLoader.discover(str(root / "tests"))
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
print(stream.getvalue())
(root / "results").mkdir(exist_ok=True)
(root / "results/python-tests.txt").write_text(stream.getvalue(), encoding="utf-8")
(root / "results/python-tests.json").write_text(
    json.dumps(
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "successful": result.wasSuccessful(),
        },
        indent=2,
    )
)
sys.exit(0 if result.wasSuccessful() else 1)
