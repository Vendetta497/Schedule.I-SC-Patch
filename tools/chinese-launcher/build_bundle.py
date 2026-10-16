"""Build a portable local launcher without redistributing a font in the repository."""

import argparse
import hashlib
import importlib
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


def download_pip(cache):
    metadata_url = "https://pypi.org/pypi/pip/25.1.1/json"
    with urllib.request.urlopen(metadata_url, timeout=60) as response:
        metadata = json.load(response)
    entry = next(item for item in metadata["urls"] if item["filename"] == "pip-25.1.1-py3-none-any.whl")
    if not entry["url"].startswith("https://files.pythonhosted.org/"):
        raise RuntimeError("Unexpected pip download host")
    wheel = cache / entry["filename"]
    if not wheel.exists():
        with urllib.request.urlopen(entry["url"], timeout=60) as response, wheel.open("xb") as stream:
            shutil.copyfileobj(response, stream)
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != entry["digests"]["sha256"]:
        raise RuntimeError("pip wheel checksum failed")
    return wheel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--font-number", type=int, default=0)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--zip", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    site = output / "runtime/Lib/site-packages"
    site.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)
    wheel = download_pip(args.cache)
    # Isolated pip uses the public PyPI index and installs only inside this bundle.
    bootstrap = (
        "import sys; sys.path.insert(0,sys.argv.pop(1)); "
        "from pip._internal.cli.main import main; raise SystemExit(main())"
    )
    pip_command = [
        sys.executable, "-c", bootstrap, str(wheel), "--isolated", "--disable-pip-version-check",
        "install", "--no-input", "--no-compile", "--no-cache-dir", "--index-url", "https://pypi.org/simple",
        "--target", str(site),
    ]
    # tpk_ar 0.2.4 is a pure-Python sdist. The embedded interpreter needs a local
    # build backend; binary-only installation for every package would reject it.
    subprocess.run(pip_command + ["--only-binary=:all:", "setuptools==80.9.0", "wheel==0.45.1"], check=True)
    subprocess.run(pip_command + [
        "--upgrade", "--only-binary=:all:", "--no-binary=tpk_ar", "--no-build-isolation",
        "--requirement", str(source / "requirements.txt"),
    ], check=True)
    sys.path.insert(0, str(site))
    sys.path.insert(0, str(source))
    # This site directory did not exist when the embedded interpreter started.
    # Drop negative import-cache entries before loading the freshly installed packages.
    importlib.invalidate_caches()
    from fontTools.ttLib import TTFont
    from font_repair import chinese_supported
    fonts = output / "fonts"
    fonts.mkdir(exist_ok=True)
    data = args.font.read_bytes()
    if data[:4] == b"ttcf":
        with TTFont(io.BytesIO(data), fontNumber=args.font_number) as font:
            stream = io.BytesIO()
            font.save(stream)
            data = stream.getvalue()
    if not chinese_supported(data):
        raise RuntimeError("Selected font does not cover the launcher's Chinese sample")
    (fonts / "chinese.ttf").write_bytes(data)
    for name in ("font_repair.py", "launcher.py", "README.md"):
        shutil.copy2(source / name, output / name)
    shutil.copy2(source / "setup.cmd", output / "生成Steam启动选项.cmd")
    record = {
        "launcher_version": "1.0", "python_version": "3.13.5",
        "font_source_name": args.font.name, "font_number": args.font_number,
        "font_sha256": hashlib.sha256(data).hexdigest(),
        "game_or_steam_settings_changed_during_build": False,
    }
    (output / "build.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    files = [path for path in sorted(output.rglob("*"))
             if path.is_file() and "__pycache__" not in path.parts]
    checksums = {path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in files}
    (output / "files-sha256.json").write_text(json.dumps(checksums, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.zip:
        target = args.zip.resolve()
        if target.is_relative_to(output):
            raise RuntimeError("ZIP output must be outside the launcher directory")
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in files + [output / "files-sha256.json"]:
                archive.write(path, "ScheduleI-ChineseLauncher/" + path.relative_to(output).as_posix())
        with zipfile.ZipFile(target) as archive:
            if archive.testzip():
                raise RuntimeError("Launcher ZIP CRC check failed")
            for relative, expected in checksums.items():
                actual = hashlib.sha256(archive.read("ScheduleI-ChineseLauncher/" + relative)).hexdigest()
                if actual != expected:
                    raise RuntimeError(f"Launcher ZIP checksum failed: {relative}")
        record["zip_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    print(json.dumps(record, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
