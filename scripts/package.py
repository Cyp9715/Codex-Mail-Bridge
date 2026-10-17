"""Build distributable ZIPs from an explicit source allowlist, never mail data."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re
import zipfile
from publication_guard import content_findings, load_denylist, path_findings

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/codex-mail-bridge"
TEXT_SUFFIXES = {".py", ".cjs", ".cmd", ".ps1", ".json", ".md"}


def validate_file(path, data=None):
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Symlinks are not allowed in releases")
    data = path.read_bytes() if data is None else data
    findings = path_findings(path.relative_to(ROOT).as_posix()) + content_findings(data, load_denylist(ROOT))
    if findings:
        raise ValueError("Publication check failed: " + ", ".join(sorted(set(findings))))
    if path.suffix not in TEXT_SUFFIXES | {".png"} and path.name not in {"LICENSE", ".gitignore", ".gitattributes", "pre-commit", "commit-msg", "pre-push"}:
        raise ValueError("Unexpected release file type: " + path.name)
    if path.suffix == ".png":
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Invalid PNG")
        return
    text = data.decode("utf-8")
    for email in re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text):
        if not email.lower().endswith(".test"):
            raise ValueError("Non-test email address found in " + path.name)
    if re.search(r"[A-Za-z]:[\\/]+Users[\\/]+[^<%\s]", text):
        raise ValueError("Personal Windows path found in " + path.name)
    if path.suffix == ".py":
        ast.parse(text)
    if path.suffix == ".json":
        json.loads(text)


def package(destination, files):
    # Inspect every input before creating even a partial distributable archive.
    snapshots = []
    for path, relative in files:
        data = path.read_bytes()
        validate_file(path, data)
        snapshots.append((relative, data))
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, data in snapshots:
            entry = zipfile.ZipInfo(relative)
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = (0o100755 if relative.startswith(".githooks/") else 0o100644) << 16
            archive.writestr(entry, data)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive verification failed")
        for name in archive.namelist():
            if name.startswith(("/", "\\")) or ".." in Path(name).parts:
                raise ValueError("Unsafe archive path")
    return {"file": destination.name, "files": len(files), "bytes": destination.stat().st_size,
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}


def validate_manifests(manifest, overlay):
    version = manifest["version"]
    if version != overlay["version"] or manifest["name"] != overlay["name"]:
        raise ValueError("Manifest identity/version mismatch")
    if manifest["$schema"] != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise ValueError("Wrong portable manifest format")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Expected semantic version")
    interface = manifest["extensions"]["com.openai"]["interface"]
    author = manifest.get("author")
    if not isinstance(author, dict) or author != overlay.get("author"):
        raise ValueError("Portable/compatibility author mismatch")
    publisher = author.get("name")
    if not isinstance(publisher, str) or not publisher.strip() or publisher != interface.get("developerName"):
        raise ValueError("Author and developer attribution must match")
    if interface != overlay.get("interface") or manifest.get("description") != overlay.get("description"):
        raise ValueError("Portable/compatibility listing mismatch")
    openai = manifest["extensions"]["com.openai"]
    if openai.get("requires_local_executor") is not True or overlay.get("requires_local_executor") is not True:
        raise ValueError("Local mail access must declare desktop execution")
    for configuration in (manifest, openai, overlay):
        if any(configuration.get(key) is not None for key in ("mcpServers", "apps", "hooks")):
            raise ValueError("The skills-only release must not declare MCP servers, apps or hooks")
    if len(interface["longDescription"]) > 4000:
        raise ValueError("Listing description is too long")
    if len(interface["displayName"]) > 30 or len(interface["shortDescription"]) > 30:
        raise ValueError("Listing name/subtitle is too long")
    prompts = interface.get("defaultPrompt")
    if prompts is not None:
        values = [prompts] if isinstance(prompts, str) else prompts
        if not isinstance(values, list) or not 1 <= len(values) <= 3 or not all(isinstance(p, str) and p.strip() for p in values):
            raise ValueError("Expected one default prompt or up to three nonblank prompt strings")
    return version


def validate_runtime_version(source, version):
    tree = ast.parse(source)
    versions = [node.value.value for node in tree.body
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                and any(isinstance(target, ast.Name) and target.id == "VERSION"
                        for target in node.targets)]
    if versions != [version]:
        raise ValueError("CLI runtime and manifest version mismatch")


def validate_marketplace(catalog):
    entries = catalog.get("plugins", [])
    if catalog.get("name") != "cyp-soft-local" or len(entries) != 1:
        raise ValueError("Unexpected local marketplace identity")
    entry = entries[0]
    if (entry.get("name") != "codex-mail-bridge"
            or entry.get("source") != {"source": "local", "path": "./plugins/codex-mail-bridge"}
            or entry.get("policy") != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}):
        raise ValueError("Local marketplace must resolve the packaged plugin")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
    overlay = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    version = validate_manifests(manifest, overlay)
    validate_runtime_version((PLUGIN / "server/bridge.py").read_text(encoding="utf-8"), version)
    validate_marketplace(json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")))
    # Include only known component directories and explicit top-level files.
    for name in ("mcp.json", ".mcp.json", ".app.json", "hooks/hooks.json"):
        if (PLUGIN / name).exists():
            raise ValueError("The skills-only release contains a server/app/hook configuration")
    plugin_files = [PLUGIN / name for name in (
        "plugin.json", ".codex-plugin/plugin.json",
        "README.md", "INSTALL.md", "LICENSE", "THIRD_PARTY_NOTICES.md")]
    for name in ("server", "scripts", "skills", "tests", "assets", "docs"):
        plugin_files += sorted(p for p in (PLUGIN / name).rglob("*")
                               if p.is_file() and "__pycache__" not in p.parts)
    plugin_files = sorted(set(plugin_files))
    installer_files = [ROOT / name for name in (
        "INSTALL.md", "install-local.cmd", "scripts/install-local.cjs", ".agents/plugins/marketplace.json")]
    source_files = plugin_files + installer_files + [ROOT / name for name in (
        "README.md", "README.ko.md", "AGENTS.md", "LICENSE", "THIRD_PARTY_NOTICES.md", ".gitignore",
        ".gitattributes", ".agents/plugins/marketplace.json", "scripts/package.py", "scripts/publication_guard.py",
        "scripts/run_publication_guard.cjs", "scripts/qa_host_handoff.py", "scripts/verify_local_install.py")]
    source_files += sorted((ROOT / ".githooks").glob("*"))
    source_files += sorted((ROOT / "scripts/tests").glob("test_*"))
    source_files += sorted((ROOT / "docs").glob("*.md"))
    results = [package(args.output / f"codex-mail-bridge-{version}-plugin.zip",
                       [(p, p.relative_to(PLUGIN).as_posix()) for p in plugin_files]),
               package(args.output / f"codex-mail-bridge-{version}-source.zip",
                       [(p, p.relative_to(ROOT).as_posix()) for p in sorted(set(source_files))])]
    print(json.dumps({"version": version, "artifacts": results}, indent=2))


if __name__ == "__main__":
    main()
