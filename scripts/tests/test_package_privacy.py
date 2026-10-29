"""Release archives must contain exactly the bytes checked before writing."""
from pathlib import Path
import copy
import json
import shutil
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

    def test_distribution_rejects_retired_runtime_modules(self):
        runtime = self.root / "server"
        shutil.copytree(builder.PLUGIN / "server", runtime, ignore=shutil.ignore_patterns("__pycache__"))
        (runtime / "retired_adapter.py").write_text("# obsolete adapter", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "runtime files"):
            builder.validate_runtime_files(runtime)

    def test_distribution_requires_the_complete_thunderbird_runtime(self):
        runtime = self.root / "server"
        shutil.copytree(builder.PLUGIN / "server", runtime, ignore=shutil.ignore_patterns("__pycache__"))
        builder.validate_runtime_files(runtime)
        (runtime / "accounts.py").unlink()
        with self.assertRaisesRegex(ValueError, "runtime files"):
            builder.validate_runtime_files(runtime)

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


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((builder.PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.overlay = json.loads((builder.PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))

    def test_release_listings_are_synchronized(self):
        self.assertEqual(builder.validate_manifests(self.manifest, self.overlay), self.manifest["version"])

    def test_excess_default_prompts_cannot_be_packaged(self):
        interface = self.manifest["extensions"]["com.openai"]["interface"]
        interface["defaultPrompt"] = ["Example prompt"] * 4
        self.overlay["interface"] = copy.deepcopy(interface)
        with self.assertRaisesRegex(ValueError, "three"):
            builder.validate_manifests(self.manifest, self.overlay)

    def test_stale_compatibility_listing_cannot_be_packaged(self):
        self.overlay["interface"]["longDescription"] = "Stale example description"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            builder.validate_manifests(self.manifest, self.overlay)

    def test_stale_compatibility_author_cannot_be_packaged(self):
        self.overlay["author"]["name"] = "Different author"
        with self.assertRaisesRegex(ValueError, "author mismatch"):
            builder.validate_manifests(self.manifest, self.overlay)

    def test_conflicting_developer_attribution_cannot_be_packaged(self):
        self.manifest["extensions"]["com.openai"]["interface"]["developerName"] = "Different author"
        self.overlay["interface"]["developerName"] = "Different author"
        with self.assertRaisesRegex(ValueError, "attribution must match"):
            builder.validate_manifests(self.manifest, self.overlay)

    def test_local_requirement_cannot_be_hidden(self):
        self.manifest["extensions"]["com.openai"]["requires_local_executor"] = False
        with self.assertRaisesRegex(ValueError, "desktop"):
            builder.validate_manifests(self.manifest, self.overlay)

    def test_mcp_app_or_hook_declarations_cannot_reenter_skill_only_release(self):
        for key in ("mcpServers", "apps", "hooks"):
            manifest = copy.deepcopy(self.manifest)
            manifest["extensions"]["com.openai"][key] = "./unexpected.json"
            with self.assertRaisesRegex(ValueError, "skills-only"):
                builder.validate_manifests(manifest, self.overlay)

    def test_stale_runtime_cannot_be_packaged(self):
        with self.assertRaisesRegex(ValueError, "runtime.*mismatch"):
            builder.validate_runtime_version('VERSION = "0.1.0"', "0.2.0")
        builder.validate_runtime_version('VERSION = "0.2.0"', "0.2.0")

    def test_marketplace_must_resolve_the_packaged_local_plugin(self):
        catalog = json.loads((builder.ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        builder.validate_marketplace(catalog)
        catalog["plugins"][0]["source"]["path"] = "./missing-plugin"
        with self.assertRaisesRegex(ValueError, "resolve"):
            builder.validate_marketplace(catalog)


if __name__ == "__main__":
    unittest.main()
