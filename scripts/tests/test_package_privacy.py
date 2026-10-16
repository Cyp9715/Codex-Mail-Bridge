"""Release archives must contain exactly the bytes checked before writing."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package as builder


class PackagePrivacyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True, capture_output=True)
        self.root_patch = patch.object(builder, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_private_input_prevents_archive_creation(self):
        good = self.root / "README.md"
        bad = self.root / "notes.md"
        good.write_text("Synthetic source", encoding="utf-8")
        bad.write_text("someone@" + "example.invalid", encoding="utf-8")
        output = self.root / "release.zip"
        with self.assertRaises(ValueError):
            builder.package(output, [(good, good.name), (bad, bad.name)])
        self.assertFalse(output.exists())

    def test_private_denylist_applies_to_release_inputs(self):
        private = self.root / "private/publication-denylist.json"
        private.parent.mkdir()
        private.write_text('["private-project-marker"]', encoding="utf-8")
        source = self.root / "README.md"
        source.write_text("private-project-marker", encoding="utf-8")
        with self.assertRaises(ValueError):
            builder.package(self.root / "release.zip", [(source, source.name)])

    def test_archive_uses_validated_snapshot_and_preserves_hook_mode(self):
        source = self.root / "hook.md"
        source.write_text("Synthetic safe source", encoding="utf-8")
        validate = builder.validate_file
        def change_after_validation(path, data=None):
            validate(path, data)
            path.write_text("someone@" + "example.invalid", encoding="utf-8")
        output = self.root / "release.zip"
        with patch.object(builder, "validate_file", side_effect=change_after_validation):
            builder.package(output, [(source, ".githooks/pre-commit")])
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read(".githooks/pre-commit"), b"Synthetic safe source")
            self.assertEqual(archive.getinfo(".githooks/pre-commit").external_attr >> 16, 0o100755)


if __name__ == "__main__":
    unittest.main()
