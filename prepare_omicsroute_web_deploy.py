from __future__ import annotations

import ast
import importlib.metadata as metadata
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.cwd()
APP = ROOT / "app.py"
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"

CONFIG_DIR = ROOT / ".streamlit"
CONFIG_FILE = CONFIG_DIR / "config.toml"
REQUIREMENTS = ROOT / "requirements.txt"
GITIGNORE = ROOT / ".gitignore"
REPORT = ROOT / "WEB_DEPLOYMENT_REPORT.md"
GUIDE = ROOT / "WEB_DEPLOYMENT.md"

DESKTOP_ONLY_DISTS = {
    "pyinstaller",
    "pyinstaller-hooks-contrib",
    "pywebview",
    "pythonnet",
    "clr-loader",
}

# Packages that should never appear in a pip requirements file.
STDLIB = set(getattr(sys, "stdlib_module_names", set()))
STDLIB.update({
    "__future__", "typing", "pathlib", "os", "sys", "json", "csv", "re",
    "math", "statistics", "datetime", "time", "subprocess", "socket",
    "threading", "tempfile", "shutil", "collections", "dataclasses",
    "functools", "itertools", "hashlib", "urllib", "webbrowser", "atexit",
    "enum", "logging", "traceback", "copy", "inspect", "io", "textwrap",
})


def fail(message: str) -> None:
    print("")
    print("=" * 72)
    print("RESULT: FAIL")
    print(message)
    raise SystemExit(1)


def ensure_venv_python() -> None:
    """
    If the user runs the script outside .venv, transparently rerun it with the
    OmicsRoute virtual environment so dependency versions come from the real app.
    """
    if not VENV_PY.exists():
        fail(f"OmicsRoute virtual environment was not found: {VENV_PY}")

    current = Path(sys.executable).resolve()
    expected = VENV_PY.resolve()

    if current != expected:
        print("Re-running deployment prep with OmicsRoute .venv Python...")
        result = subprocess.run(
            [str(expected), str(Path(__file__).resolve())],
            cwd=ROOT,
        )
        raise SystemExit(result.returncode)


def resolve_local_module(module_name: str) -> Path | None:
    """
    Resolve the longest local module path available from an import name.
    Example: engine.scoring -> engine/scoring.py
    """
    parts = module_name.split(".")

    for end in range(len(parts), 0, -1):
        partial = parts[:end]

        py_file = ROOT.joinpath(*partial).with_suffix(".py")
        if py_file.exists():
            return py_file

        package_init = ROOT.joinpath(*partial, "__init__.py")
        if package_init.exists():
            return package_init

    return None


def parse_imports(path: Path) -> set[str]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except Exception as exc:
        fail(f"Could not parse {path.relative_to(ROOT)}: {exc}")

    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                imports.add(node.module)

    return imports


def collect_reachable_sources_and_external_imports() -> tuple[set[Path], set[str]]:
    pending = [APP]
    visited: set[Path] = set()
    external: set[str] = set()

    while pending:
        path = pending.pop()
        path = path.resolve()

        if path in visited:
            continue

        visited.add(path)

        for module_name in parse_imports(path):
            top = module_name.split(".")[0]

            if top in STDLIB:
                continue

            local_path = resolve_local_module(module_name)

            if local_path is not None:
                resolved = local_path.resolve()
                if resolved not in visited:
                    pending.append(resolved)
            else:
                external.add(top)

    return visited, external


def installed_distribution_versions(external_imports: set[str]) -> tuple[list[str], list[str]]:
    package_map = metadata.packages_distributions()
    requirements: dict[str, str] = {}
    unresolved: list[str] = []

    for import_name in sorted(external_imports):
        distributions = package_map.get(import_name, [])

        if not distributions:
            # Common import/distribution naming differences.
            manual = {
                "yaml": ["PyYAML"],
                "sklearn": ["scikit-learn"],
                "Bio": ["biopython"],
                "PIL": ["Pillow"],
                "bs4": ["beautifulsoup4"],
                "cv2": ["opencv-python"],
            }
            distributions = manual.get(import_name, [])

        if not distributions:
            unresolved.append(import_name)
            continue

        # Prefer one concrete distribution for each import.
        dist_name = distributions[0]

        if dist_name.lower() in DESKTOP_ONLY_DISTS:
            continue

        try:
            version = metadata.version(dist_name)
        except metadata.PackageNotFoundError:
            unresolved.append(import_name)
            continue

        requirements[dist_name] = version

    # Ensure Streamlit is explicitly pinned for deployment stability.
    try:
        requirements["streamlit"] = metadata.version("streamlit")
    except metadata.PackageNotFoundError:
        fail("Streamlit is not installed in the OmicsRoute virtual environment.")

    lines = [
        f"{name}=={version}"
        for name, version in sorted(
            requirements.items(),
            key=lambda x: x[0].lower(),
        )
    ]

    return lines, unresolved


def merge_gitignore() -> None:
    managed = [
        "",
        "# OmicsRoute local/development artifacts",
        ".venv/",
        "__pycache__/",
        "*.py[cod]",
        ".pytest_cache/",
        ".mypy_cache/",
        "build/",
        "release/",
        "backups/",
        "logs/",
        "desktop_app/",
        "launcher/",
        "*.spec",
        ".DS_Store",
        "Thumbs.db",
        "install_bioflow_*.py",
        "build_bioflow_exe.py",
        "apply_*.py",
        "",
    ]

    existing = ""
    if GITIGNORE.exists():
        existing = GITIGNORE.read_text(encoding="utf-8")

    additions = [
        line
        for line in managed
        if line and line not in existing.splitlines()
    ]

    content = existing.rstrip()

    if additions:
        if content:
            content += "\n\n"
        content += "\n".join([
            "# OmicsRoute local/development artifacts",
            *[line for line in additions if line != "# OmicsRoute local/development artifacts"],
        ])

    GITIGNORE.write_text(content.rstrip() + "\n", encoding="utf-8")


def scan_portability_warnings(sources: set[Path]) -> list[str]:
    warnings: list[str] = []

    patterns = {
        r"[A-Za-z]:\\Users\\": "Windows user-specific absolute path",
        r"/mnt/data/": "temporary sandbox path",
        r"\.venv[\\/]+": "direct .venv path reference",
    }

    for path in sorted(sources):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue

        for pattern, label in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                warnings.append(
                    f"{path.relative_to(ROOT)}: {label}"
                )

    return sorted(set(warnings))


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def run_web_smoke_test() -> tuple[bool, str]:
    port = free_port()
    log_path = ROOT / "WEB_DEPLOYMENT_SMOKE_TEST.log"

    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            [
                str(VENV_PY),
                "-m",
                "streamlit",
                "run",
                str(APP),
                "--server.headless=true",
                "--server.address=127.0.0.1",
                f"--server.port={port}",
                "--server.fileWatcherType=none",
                "--browser.gatherUsageStats=false",
            ],
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
        )

        try:
            deadline = time.time() + 25

            while time.time() < deadline:
                if proc.poll() is not None:
                    return False, str(log_path)

                if port_open(port):
                    return True, str(log_path)

                time.sleep(0.25)

            return False, str(log_path)

        finally:
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass


def main() -> None:
    print("=" * 72)
    print("OmicsRoute Web Deployment Prep v1")
    print("=" * 72)

    if not APP.exists():
        fail("Run this script from the OmicsRoute project root. app.py was not found.")

    ensure_venv_python()

    sources, external_imports = collect_reachable_sources_and_external_imports()
    requirement_lines, unresolved = installed_distribution_versions(external_imports)
    portability_warnings = scan_portability_warnings(sources)

    REQUIREMENTS.write_text(
        "\n".join(requirement_lines) + "\n",
        encoding="utf-8",
    )

    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(
        """[server]
headless = true
fileWatcherType = "none"

[browser]
gatherUsageStats = false
""",
        encoding="utf-8",
    )

    merge_gitignore()

    GUIDE.write_text(
        """# OmicsRoute Web Deployment

OmicsRoute is prepared for deployment on Streamlit Community Cloud.

## Repository contents that must be on GitHub

Keep:
- app.py
- data/
- engine/
- services/
- requirements.txt
- .streamlit/config.toml
- any other project source files imported by app.py

Do not upload:
- .venv/
- build/
- release/
- backups/
- logs/

## Deploy

1. Push the OmicsRoute project to a GitHub repository.
2. Open https://share.streamlit.io
3. Click **Create app**.
4. Select the OmicsRoute GitHub repository.
5. Branch: normally `main`.
6. Entrypoint: `app.py`.
7. In Advanced settings, choose the same Python major/minor version you use
   locally when possible.
8. Deploy.

The deployed application receives a `*.streamlit.app` URL that works on
Windows, macOS, Linux, phones, and tablets through a browser.
""",
        encoding="utf-8",
    )

    smoke_ok, smoke_log = run_web_smoke_test()

    report_lines = [
        "# OmicsRoute Web Deployment Report",
        "",
        f"- Reachable Python source files: {len(sources)}",
        f"- External import names detected: {len(external_imports)}",
        f"- requirements.txt entries: {len(requirement_lines)}",
        f"- Local Streamlit smoke test: {'PASS' if smoke_ok else 'FAIL'}",
        "",
        "## Generated requirements",
        "",
        "```text",
        *requirement_lines,
        "```",
        "",
    ]

    if unresolved:
        report_lines += [
            "## Unresolved imports",
            "",
            *[f"- {name}" for name in unresolved],
            "",
        ]

    if portability_warnings:
        report_lines += [
            "## Portability warnings",
            "",
            *[f"- {item}" for item in portability_warnings],
            "",
        ]
    else:
        report_lines += [
            "## Portability warnings",
            "",
            "- None detected in reachable OmicsRoute source files.",
            "",
        ]

    report_lines += [
        "## Smoke-test log",
        "",
        f"`{Path(smoke_log).name}`",
        "",
    ]

    REPORT.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print(f"Reachable source files: {len(sources)}")
    print(f"requirements.txt entries: {len(requirement_lines)}")
    print(f"Unresolved imports: {len(unresolved)}")
    print(f"Portability warnings: {len(portability_warnings)}")
    print(f"Local Streamlit smoke test: {'PASS' if smoke_ok else 'FAIL'}")
    print(f"Report: {REPORT}")
    print("")

    if not smoke_ok:
        fail(
            "Web deployment files were generated, but the local Streamlit "
            f"smoke test failed. See: {smoke_log}"
        )

    if unresolved:
        print(
            "WARNING: Some imports could not be mapped automatically. "
            "Review WEB_DEPLOYMENT_REPORT.md before publishing."
        )

    print("=" * 72)
    print("RESULT: PASS")
    print("OmicsRoute is prepared for GitHub + Streamlit Community Cloud deployment.")
    print("Next: push the project to GitHub, then deploy app.py on Streamlit Cloud.")


if __name__ == "__main__":
    main()
