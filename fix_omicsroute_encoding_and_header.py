from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

root = Path.cwd()
app = root / "app.py"
backups = root / "backups"
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

if not app.exists():
    raise SystemExit("ERROR: Run this script from the OmicsRoute project root.")

backups.mkdir(parents=True, exist_ok=True)
backup = backups / f"app_before_encoding_repair_{stamp}.py"
shutil.copy2(app, backup)

text = app.read_text(encoding="utf-8-sig")

def badness(s: str) -> int:
    markers = ("â", "Ã", "Â", "ğŸ", "Ä", "Å", "ðŸ", "�")
    return sum(s.count(m) for m in markers)

before = badness(text)
repaired = text

# The previous PowerShell Get-Content command on Turkish Windows read UTF-8
# as Windows-1254 and then wrote that mojibake back as UTF-8.
if before:
    try:
        candidate = text.encode("cp1254").decode("utf-8")
        if badness(candidate) < before:
            repaired = candidate
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

# Final public-facing brand cleanup.
repaired = repaired.replace(
    "BIOFLOW • WEB RELEASE CANDIDATE",
    "OMICSROUTE • WEB RELEASE CANDIDATE",
)
repaired = repaired.replace("BioFlow", "OmicsRoute")

app.write_text(repaired, encoding="utf-8")

# Syntax check.
python = root / ".venv" / "Scripts" / "python.exe"
if not python.exists():
    python = Path(sys.executable)

result = subprocess.run(
    [str(python), "-m", "py_compile", str(app)],
    cwd=root,
    capture_output=True,
    text=True,
)

if result.returncode != 0:
    shutil.copy2(backup, app)
    print("RESULT: FAIL")
    print("Syntax check failed; original app.py was restored.")
    print(result.stderr or result.stdout)
    raise SystemExit(1)

final_text = app.read_text(encoding="utf-8")
remaining_visible = final_text.count("BioFlow") + final_text.count("BIOFLOW")

print("=" * 72)
print("OmicsRoute encoding + branding repair")
print("=" * 72)
print(f"Mojibake markers before: {before}")
print(f"Mojibake markers after:  {badness(final_text)}")
print(f"Visible BioFlow/BIOFLOW strings remaining in app.py: {remaining_visible}")
print(f"Backup: {backup}")
print("")
print("RESULT: PASS")
print("app.py encoding and OmicsRoute header were repaired.")
