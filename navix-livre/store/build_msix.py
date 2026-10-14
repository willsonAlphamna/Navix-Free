#!/usr/bin/env python3
"""Prepare an unsigned MSIX for Microsoft Store submission, never installation.

Windows packing uses the Windows SDK MakeAppx schema validator. --no-pack
only stages files and can run on Linux; it does not certify Store acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from navix_livre import VERSION

FOUNDATION = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
UAP = "http://schemas.microsoft.com/appx/manifest/uap/windows10"
RESCAP = "http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
for prefix, namespace in (("", FOUNDATION), ("uap", UAP), ("rescap", RESCAP)):
    ET.register_namespace(prefix, namespace)
EXECUTABLES = ("NavixLivre.exe", "NavixBridge.exe")
DOCUMENTS = ("README.md", "COMO_INSTALAR.md", "PRIVACIDADE.md", "LICENSE")
LOGOS = {"StoreLogo.png": 50, "Square44x44Logo.png": 44, "Square150x150Logo.png": 150}


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def msix_version(version):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("App version must have exactly three numeric components")
    parts = [int(part) for part in version.split(".")]
    if any(part > 65535 for part in parts):
        raise ValueError("MSIX version components must be at most 65535")
    # The Store reserves the fourth component; submissions must use zero.
    return ".".join(map(str, parts + [0]))


def validate_identity(name, publisher, display_name):
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)}
    if not re.fullmatch(r"[A-Za-z0-9.-]{3,50}", name) or name.upper() in reserved:
        raise ValueError("Identity Name must be the 3–50 character Partner Center package name")
    if not publisher.startswith("CN=") or not 4 <= len(publisher) <= 8192:
        raise ValueError("Publisher must be the exact Partner Center X.500 CN= identity")
    if "OID.2.25.311729368913984317654407730594956997722" in publisher:
        raise ValueError("Unsigned-installation publisher markers are not permitted")
    if not display_name.strip() or len(display_name) > 256:
        raise ValueError("Publisher display name must contain 1–256 characters")
    if any(ord(char) < 32 for char in publisher + display_name):
        raise ValueError("Publisher fields must not contain control characters")
    # The Windows SDK validates the full distinguished-name grammar when packing.


def manifest(name, publisher, display_name, version):
    def child(parent, tag, attributes=None, text=None, namespace=FOUNDATION):
        element = ET.SubElement(parent, f"{{{namespace}}}{tag}", attributes or {})
        element.text = text
        return element

    root = ET.Element(f"{{{FOUNDATION}}}Package", {"IgnorableNamespaces": "uap rescap"})
    child(root, "Identity", {"Name": name, "Publisher": publisher,
                            "Version": version, "ProcessorArchitecture": "x64"})
    properties = child(root, "Properties")
    child(properties, "DisplayName", text="Navix Livre")
    child(properties, "PublisherDisplayName", text=display_name)
    child(properties, "Logo", text="Assets\\StoreLogo.png")
    dependencies = child(root, "Dependencies")
    child(dependencies, "TargetDeviceFamily", {"Name": "Windows.Desktop",
          "MinVersion": "10.0.19041.0", "MaxVersionTested": "10.0.26100.0"})
    child(child(root, "Resources"), "Resource", {"Language": "pt-BR"})
    application = child(child(root, "Applications"), "Application", {
        "Id": "NavixLivre", "Executable": "NavixLivre.exe",
        "EntryPoint": "Windows.FullTrustApplication"})
    child(application, "VisualElements", {"DisplayName": "Navix Livre",
          "Description": "Painel Windows e ponte MCP local, com permissões opcionais.",
          "BackgroundColor": "transparent", "Square150x150Logo": "Assets\\Square150x150Logo.png",
          "Square44x44Logo": "Assets\\Square44x44Logo.png"}, namespace=UAP)
    child(child(root, "Capabilities"), "Capability", {"Name": "runFullTrust"}, namespace=RESCAP)
    ET.indent(root)
    return ET.ElementTree(root)


def stage_package(dist, destination, name, publisher, display_name, source_commit=None):
    from PIL import Image

    validate_identity(name, publisher, display_name)
    version = msix_version(VERSION)
    sources = {filename: Path(dist) / filename for filename in EXECUTABLES}
    sources.update({filename: PROJECT / filename for filename in DOCUMENTS})
    icon = PROJECT / "assets" / "navix.ico"
    for path in (*sources.values(), icon):
        if not path.is_file():
            raise ValueError(f"Missing build input: {path}")
    if source_commit is not None and not re.fullmatch(r"[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", source_commit):
        raise ValueError("Source commit must be a complete Git commit hash")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for filename, source in sources.items():
        shutil.copyfile(source, destination / filename)
    (destination / "Assets").mkdir()
    with Image.open(icon) as source:
        source = source.convert("RGBA")
        for filename, size in LOGOS.items():
            source.resize((size, size), Image.Resampling.LANCZOS).save(destination / "Assets" / filename)
    manifest(name, publisher, display_name, version).write(
        destination / "AppxManifest.xml", encoding="utf-8", xml_declaration=True)
    if source_commit is None and shutil.which("git"):
        result = subprocess.run(["git", "-C", str(PROJECT), "rev-parse", "HEAD"],
                                capture_output=True, text=True, check=False)
        source_commit = result.stdout.strip() if result.returncode == 0 else None
    source_files = [PROJECT / filename for filename in
                    ("navix_livre.py", "navix_gui.py", "navix_remote.py", "make_assets.py")]
    source_files += [Path(__file__).resolve(), icon]
    info = {"application_version": VERSION, "package_version": version,
            "identity_name": name, "publisher": publisher,
            "publisher_display_name": display_name, "source_commit": source_commit,
            "signing_status": "unsigned-store-submission", "installable_release": False,
            "source_sha256": {path.relative_to(PROJECT).as_posix(): sha256(path) for path in source_files},
            "payload_sha256": {path.relative_to(destination).as_posix(): sha256(path)
                               for path in sorted(destination.rglob("*")) if path.is_file()}}
    (destination / "BUILD_INFO.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return info


def verify_unpacked(staged, unpacked, info):
    staged, unpacked = Path(staged), Path(unpacked)
    identity = ET.parse(unpacked / "AppxManifest.xml").getroot().find(f"{{{FOUNDATION}}}Identity")
    expected = {"Name": info["identity_name"], "Publisher": info["publisher"],
                "Version": info["package_version"], "ProcessorArchitecture": "x64"}
    if identity is None or identity.attrib != expected:
        raise ValueError("Unpacked package identity differs from the requested identity")
    expected_files = {path.relative_to(staged).as_posix(): sha256(path)
                      for path in staged.rglob("*") if path.is_file()}
    for filename, digest in expected_files.items():
        path = unpacked / filename
        if not path.is_file() or sha256(path) != digest:
            raise ValueError(f"Unpacked payload is missing or modified: {filename}")
    extra = {path.relative_to(unpacked).as_posix() for path in unpacked.rglob("*") if path.is_file()}
    extra -= expected_files.keys() | {"AppxBlockMap.xml", "[Content_Types].xml"}
    if extra:
        raise ValueError(f"Unexpected package contents: {sorted(extra)}")


def find_makeappx():
    if os.name != "nt":
        raise ValueError("Packing requires Windows and the Windows SDK; use --no-pack to stage only")
    sdk = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Windows Kits" / "10" / "bin"
    candidates = list(sdk.glob("10.*/x64/makeappx.exe"))
    if not candidates:
        raise ValueError("Windows SDK x64 MakeAppx.exe was not found")
    return max(candidates, key=lambda path: tuple(map(int, path.parent.parent.name.split("."))))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity-name", required=True)
    parser.add_argument("--publisher", required=True)
    parser.add_argument("--publisher-display-name", required=True)
    parser.add_argument("--dist", type=Path, default=PROJECT / "dist")
    parser.add_argument("--output", type=Path, required=True,
                        help="New .msix file, or new staging directory with --no-pack")
    parser.add_argument("--source-commit")
    parser.add_argument("--no-pack", action="store_true", help="Stage only; no installable package is created")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    try:
        if output.exists():
            raise ValueError(f"Output already exists: {output}")
        if not args.no_pack and output.suffix.lower() != ".msix":
            raise ValueError("Packed output must end with .msix")
        validate_identity(args.identity_name, args.publisher, args.publisher_display_name)
        tool = None if args.no_pack else find_makeappx()
        with tempfile.TemporaryDirectory(prefix="navix-store-") as temporary:
            temporary = Path(temporary)
            stage = temporary / "staging"
            info = stage_package(args.dist, stage, args.identity_name, args.publisher,
                                 args.publisher_display_name, args.source_commit)
            if args.no_pack:
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(stage, output)
            else:
                packed, unpacked = temporary / "NavixLivre.msix", temporary / "unpacked"
                subprocess.run([str(tool), "pack", "/d", str(stage), "/p", str(packed),
                                "/h", "SHA256"], check=True)
                subprocess.run([str(tool), "unpack", "/p", str(packed), "/d", str(unpacked)], check=True)
                verify_unpacked(stage, unpacked, info)
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(packed, output)
        print(f"Prepared unsigned Store submission only: {output}")
        print("Not an installable release. Microsoft Store certification and signing are still required.")
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
