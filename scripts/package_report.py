"""Zip report/main.tex and report/figures/ for upload to Overleaf (main.tex at the zip root)."""

import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "report"
tex = (root / "main.tex").read_text(encoding="utf-8")

# Cheap sanity checks, since LaTeX is not compiled here.
begins = Counter(re.findall(r"\\begin\{(\w+\*?)\}", tex))
ends = Counter(re.findall(r"\\end\{(\w+\*?)\}", tex))
assert begins == ends, f"unbalanced environments: {begins - ends} {ends - begins}"
assert tex.count("{") == tex.count("}"), "unbalanced braces"
missing = [
    name
    for name in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)
    if not (root / "figures" / name).exists()
]
assert not missing, f"missing figures: {missing}"

target = root / "argument-lab-report.zip"
target.unlink(missing_ok=True)
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
    archive.write(root / "main.tex", "main.tex")
    for file in sorted((root / "figures").iterdir()):
        archive.write(file, f"figures/{file.name}")
print(f"wrote {target} ({target.stat().st_size // 1024} KiB)")
sys.exit(0)
