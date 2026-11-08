"""Create a portable coursework ZIP, excluding dependencies and the copyrighted book."""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
excluded = {
    "node_modules",
    ".npm-cache",
    ".git",
    "__pycache__",
    "book",
    "tmp",
    "test-results",
    "playwright-report",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
}
target = root / "submission/argument-lab-assignment-03.zip"
target.parent.mkdir(exist_ok=True)
with ZipFile(target, "w", ZIP_DEFLATED) as archive:
    for file in root.rglob("*"):
        relative = file.relative_to(root)
        if (
            not file.is_file()
            or any(p in excluded for p in relative.parts)
            or relative.parts[0] == "submission"
            or file.suffix == ".pyc"
            or file.name.startswith("page@")
            or file.name == ".env"
            or file.name.startswith(".env.")
            or relative.as_posix()
            in {
                "results/e2e-results.json",
                "results/python-tests.json",
                "results/python-tests.txt",
            }
        ):
            continue
        archive.write(file, Path("argument-lab") / relative)
print(target)
