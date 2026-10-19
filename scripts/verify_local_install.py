"""Verify release installation with an existing CLI and isolated synthetic data."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archives", required=True, type=Path)
    parser.add_argument("--codex", default=shutil.which("codex"))
    parser.add_argument("--previous-plugin", type=Path)
    args = parser.parse_args()
    if not args.codex or not shutil.which("node"):
        parser.error("An existing Codex CLI and Node.js are required")
    plugin = ROOT / "plugins/codex-mail-bridge"
    version = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))["version"]
    for kind, source in [("plugin", plugin), ("source", ROOT)]:
        with zipfile.ZipFile(args.archives / f"codex-mail-bridge-{version}-{kind}.zip") as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                assert not name.startswith(("/", "\\")) and ".." not in Path(name).parts
                assert archive.read(name) == (source / name).read_bytes(), name
            if kind == "plugin":
                assert "plugin.json" in archive.namelist()
                assert "INSTALL.md" in archive.namelist()
                assert "skills/mail-bridge/SKILL.md" in archive.namelist()
                assert not any(name.startswith(("plugins/", ".agents/")) for name in archive.namelist())
                assert "install-local.cmd" not in archive.namelist()
    with tempfile.TemporaryDirectory(prefix="mail-bridge-release-") as temporary:
        temporary = Path(temporary)
        source = temporary / "source with spaces"
        config = temporary / "isolated-config"
        config.mkdir()
        env = {**os.environ, "CODEX_HOME": str(config), "MAIL_BRIDGE_PYTHON": sys.executable}

        def call(command, *, data=None, expect_json=True):
            result = subprocess.run(command, cwd=source, env=env,
                                    input=json.dumps(data) if data is not None else None,
                                    capture_output=True, text=True, encoding="utf-8", timeout=60)
            assert result.returncode == 0, (command[:3], result.stderr)
            return json.loads(result.stdout) if expect_json else result.stdout

        def extract():
            with zipfile.ZipFile(args.archives / f"codex-mail-bridge-{version}-source.zip") as archive:
                archive.extractall(source)

        extract()
        installer = ["node", str(source / "scripts/install-local.cjs"), "--codex", args.codex]
        assert call([*installer, "--check"])["checkOnly"]
        assert not (config / "config.toml").exists(), "Preflight wrote user configuration"
        if os.name == "nt":
            call([os.environ["COMSPEC"], "/d", "/c", str(source / "install-local.cmd"),
                  "--check", "--codex", args.codex])

        if args.previous_plugin:
            # Upgrade at the same registered source; never touch the user's install.
            with zipfile.ZipFile(args.previous_plugin) as archive:
                archive.extractall(source / "plugins/codex-mail-bridge")
            call([args.codex, "plugin", "marketplace", "add", str(source), "--json"])
            call([args.codex, "plugin", "add", "codex-mail-bridge@cyp-soft-local", "--json"])
            extract()

        installed = call(installer)
        assert call(installer)["version"] == version  # Reinstall is idempotent.
        target = Path(installed["installedPath"])
        for file in (source / "plugins/codex-mail-bridge").rglob("*"):
            if file.is_file():
                assert file.read_bytes() == (target / file.relative_to(source / "plugins/codex-mail-bridge")).read_bytes()
        for file in target.rglob("*.md"):
            for link in re.findall(r"\]\(([^\s)]+)", file.read_text(encoding="utf-8")):
                if "://" not in link and not link.startswith("#"):
                    assert (file.parent / link.split("#")[0]).exists(), (file.name, link)

        sys.path.insert(0, str(target / "tests"))
        from create_demo import create_demo
        from attachment_demo import setup
        env.update(create_demo(temporary / "fixture"))
        env["MAIL_BRIDGE_EXPORT_ROOT"] = str(temporary / "exports")
        _, _, originals = setup(Path(env["THUNDERBIRD_HOME"]) / "Profiles/demo")

        def cli(*arguments, data=None):
            command = ["node", str(target / "scripts/mail_bridge.cjs"), *arguments]
            if data is not None:
                command.append("--arguments-stdin")
            response = call(command, data=data)
            assert response["ok"], response
            return response["result"]

        assert cli("--version")["version"] == version
        assert len(cli("--list")["operations"]) == 21
        profile = cli("--call", "thunderbird_profiles")["profiles"][0]["id"]
        cli("--call", "thunderbird_select_account", data={"profile_id": profile, "account_id": "account1", "confirm": True})
        found = cli("--call", "thunderbird_search_attachments", data={"filename": "agenda.pdf", "after": "2026-10-01"})
        message = found["messages"][0]["id"]
        listing = cli("--call", "thunderbird_list_attachments", data={"message_id": message})
        receipt = cli("--call", "thunderbird_get_attachment", data={"message_id": message, "attachment_id": listing["attachments"][0]["id"]})
        assert Path(receipt["local_path"]).read_bytes() == originals[0]
        assert receipt["sha256"] == hashlib.sha256(originals[0]).hexdigest()
        assert cli("--release", receipt["export_id"])["released"]
        assert not Path(receipt["local_path"]).exists()
    print(json.dumps({"version": version, "archive_source_bytes_match": True,
                      "local_install_and_reinstall": True, "previous_version_upgrade": bool(args.previous_plugin),
                      "installed_files_and_links": True, "synthetic_original_file_handoff": True}))


if __name__ == "__main__":
    main()
