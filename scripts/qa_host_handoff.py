"""Standalone host QA; document libraries stay outside the plugin runtime."""
from email import policy
from email.message import EmailMessage
from contextlib import closing
from io import BytesIO
from pathlib import Path
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

from docx import Document
from pypdf import PdfReader

root = Path(__file__).resolve().parents[1]
plugin = root / "plugins/codex-mail-bridge"
sys.path[:0] = [str(plugin / "server"), str(plugin / "tests")]
import accounts
from attachment_demo import pdf, setup
from create_demo import create_demo

(root / "work").mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=root / "work", prefix="synthetic-handoff-") as temporary:
    environment = create_demo(temporary)
    os.environ.update(environment)
    profile = accounts.profiles()[0]
    accounts.select_account(profile["id"], "account1", confirm=True)
    folder, _, _ = setup(profile["path"])
    document = Document()
    document.add_paragraph("Synthetic original-file handoff.")
    stream = BytesIO()
    document.save(stream)
    originals = {"agenda.pdf": pdf(), "handoff.docx": stream.getvalue()}
    message = EmailMessage(policy=policy.SMTP)
    message["Message-ID"] = "<demo-101@example.test>"
    message["From"] = "alex@example.test"
    message["To"] = "demo@example.test"
    message["Subject"] = "Project Aurora meeting"
    message.set_content("Synthetic body.")
    for name, data in originals.items():
        subtype = "pdf" if name.endswith(".pdf") else "vnd.openxmlformats-officedocument.wordprocessingml.document"
        message.add_attachment(data, maintype="application", subtype=subtype, filename=name)
    folder.write_bytes(b"From - synthetic date\r\n" + message.as_bytes())
    with closing(sqlite3.connect(profile["path"] / "global-messages-db.sqlite")) as db:
        db.execute("UPDATE messagesText_content SET c2attachmentNames=? WHERE docid=101", ("agenda.pdf handoff.docx",))
        db.commit()
    process = subprocess.Popen(["node", str(plugin / "server/launch.cjs")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, encoding="utf-8",
                               env={**os.environ, "MAIL_BRIDGE_PYTHON": sys.executable})
    serial = 0
    paths = []
    try:
        def request(method, params=None):
            global serial
            serial += 1
            process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": serial, "method": method, "params": params or {}}) + "\n")
            process.stdin.flush()
            response = json.loads(process.stdout.readline())
            assert response["id"] == serial and "error" not in response
            return response["result"]

        def tool(name, arguments):
            result = request("tools/call", {"name": name, "arguments": arguments})
            assert not result["isError"], "Synthetic tool failed"
            assert result["structuredContent"] == json.loads(result["content"][0]["text"])
            return result["structuredContent"]

        assert request("initialize", {"protocolVersion": "2025-06-18"})["serverInfo"]["version"] == "0.6.0"
        found = tool("thunderbird_search_attachments", {"filename": "handoff.docx", "after": "2026-10-01T00:00:00Z"})
        assert [m["id"] for m in found["messages"]] == [101]
        listing = tool("thunderbird_list_attachments", {"message_id": 101})
        for attachment in listing["attachments"]:
            meta = tool("thunderbird_get_attachment", {"message_id": 101, "attachment_id": attachment["id"]})
            path = Path(meta["local_path"])
            paths.append(path)
            assert path.read_bytes() == originals[attachment["name"]]
            assert meta["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
            assert meta["document_parsed"] is False
            # This is the separate host/file-tool process, not plugin parsing.
            if attachment["name"].endswith(".pdf"):
                assert "Synthetic agenda" in PdfReader(path).pages[0].extract_text()
            else:
                assert Document(path).paragraphs[0].text == "Synthetic original-file handoff."
        process.stdin.close()
        process.wait(timeout=15)
        assert process.returncode == 0 and process.stderr.read() == ""
        assert all(not path.exists() for path in paths)
    finally:
        if process.poll() is None:
            process.kill()
        process.stdout.close()
        process.stderr.close()

print(json.dumps({"files": 2, "original_bytes_and_hashes_verified": True,
                  "separate_host_pdf_and_docx_read": True, "exit_cleanup_verified": True,
                  "installed_plugin_session_verified": False}))
