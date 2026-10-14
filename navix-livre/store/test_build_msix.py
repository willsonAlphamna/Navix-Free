"""Portable staging checks; Windows CI additionally validates with MakeAppx."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from PIL import Image
from store import build_msix as msix


class StorePackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        (self.project / "assets").mkdir(parents=True)
        (self.project / "store").mkdir()
        Image.new("RGBA", (256, 256), (20, 80, 180, 255)).save(self.project / "assets" / "navix.ico")
        for filename in (*msix.DOCUMENTS, "navix_livre.py", "navix_gui.py", "navix_remote.py", "make_assets.py"):
            (self.project / filename).write_text(f"Fixture: {filename}\n", encoding="utf-8")
        (self.project / "store" / "build_msix.py").write_text("fixture build source\n", encoding="utf-8")
        self.dist = self.root / "dist"
        self.dist.mkdir()
        for filename in msix.EXECUTABLES:
            (self.dist / filename).write_bytes(b"MZfixture-only-" + filename.encode())

    def stage(self, folder="staged"):
        destination = self.root / folder
        with patch.multiple(msix, PROJECT=self.project,
                            __file__=str(self.project / "store" / "build_msix.py")):
            info = msix.stage_package(self.dist, destination, "Fixture.NavixLivre",
                                      "CN=Fixture & Testing", "A & B <Publisher>", "a" * 40)
        return destination, info

    def test_xml_escaping_identity_and_least_privilege(self):
        staged, info = self.stage()
        root = ET.parse(staged / "AppxManifest.xml").getroot()
        identity = root.find(f"{{{msix.FOUNDATION}}}Identity")
        self.assertEqual(identity.attrib["Publisher"], "CN=Fixture & Testing")
        self.assertEqual(root.find(f"{{{msix.FOUNDATION}}}Properties/{{{msix.FOUNDATION}}}PublisherDisplayName").text,
                         "A & B <Publisher>")
        self.assertEqual(root.find(f"{{{msix.FOUNDATION}}}Properties/{{{msix.FOUNDATION}}}DisplayName").text, "Navix Free")
        app = root.find(f"{{{msix.FOUNDATION}}}Applications/{{{msix.FOUNDATION}}}Application")
        visuals = app.find(f"{{{msix.UAP}}}VisualElements")
        self.assertEqual(visuals.attrib["DisplayName"], "Navix Free")
        capabilities = root.find(f"{{{msix.FOUNDATION}}}Capabilities")
        self.assertEqual([item.attrib["Name"] for item in capabilities], ["runFullTrust"])
        self.assertEqual(info["package_version"], msix.VERSION + ".0")
        self.assertEqual(info["signing_status"], "unsigned-store-submission")
        self.assertFalse(info["installable_release"])
        stored = json.loads((staged / "BUILD_INFO.json").read_text(encoding="utf-8"))
        self.assertEqual(stored["payload_sha256"]["NavixBridge.exe"], msix.sha256(self.dist / "NavixBridge.exe"))
        for filename, size in msix.LOGOS.items():
            with Image.open(staged / "Assets" / filename) as logo:
                self.assertEqual(logo.size, (size, size))

    def test_invalid_identities_and_versions_fail_before_staging(self):
        for name in ("..", "NUL", "con", "Bad Name", "../Other", "a" * 51, '<Identity Name="x">'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                msix.validate_identity(name, "CN=Fixture", "Fixture")
        for publisher in ("Fixture", "CN=", "CN=bad\nvalue", "CN=fixture, OID.2.25.311729368913984317654407730594956997722=1"):
            with self.subTest(publisher=publisher), self.assertRaises(ValueError):
                msix.validate_identity("Fixture.App", publisher, "Fixture")
        for version in ("1.2", "1.2.3.4", "1.2.65536", "1.2.3-beta"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                msix.msix_version(version)

    def test_unpack_verification_rejects_modified_and_unexpected_content(self):
        staged, info = self.stage()
        unpacked = self.root / "unpacked"
        shutil.copytree(staged, unpacked)
        (unpacked / "AppxBlockMap.xml").write_text("SDK-generated blockmap", encoding="utf-8")
        msix.verify_unpacked(staged, unpacked, info)
        (unpacked / "NavixBridge.exe").write_bytes(b"modified")
        with self.assertRaisesRegex(ValueError, "NavixBridge.exe"):
            msix.verify_unpacked(staged, unpacked, info)
        shutil.copyfile(staged / "NavixBridge.exe", unpacked / "NavixBridge.exe")
        (unpacked / "Unexpected.exe").write_bytes(b"unexpected")
        with self.assertRaisesRegex(ValueError, "Unexpected package contents"):
            msix.verify_unpacked(staged, unpacked, info)

    def test_no_missing_bridge_or_overwrite(self):
        (self.dist / "NavixBridge.exe").unlink()
        with self.assertRaisesRegex(ValueError, "Missing build input"):
            self.stage()
        self.assertFalse((self.root / "staged").exists())

    def test_staging_is_deterministic_and_preserves_existing_output(self):
        first, info = self.stage("first")
        second, repeated_info = self.stage("second")
        self.assertEqual(info, repeated_info)
        msix.verify_unpacked(first, second, info)
        with self.assertRaises(FileExistsError):
            self.stage("first")
        msix.verify_unpacked(first, second, info)

    def test_path_aliases_preserve_relative_metadata_and_hashes(self):
        alias = self.root / "directory-alias"
        try:
            alias.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"Directory symlinks unavailable: {error}")
        with patch.multiple(msix, PROJECT=alias / "project",
                            __file__=str(self.project / "store" / "build_msix.py")):
            info = msix.stage_package(alias / "dist", alias / "aliased-stage", "Fixture.NavixLivre",
                                      "CN=Fixture & Testing", "A & B <Publisher>", "a" * 40)
        self.assertEqual(info["source_sha256"]["store/build_msix.py"],
                         msix.sha256(self.project / "store" / "build_msix.py"))
        msix.verify_unpacked(self.root / "aliased-stage", alias / "aliased-stage", info)


if __name__ == "__main__":
    unittest.main()
