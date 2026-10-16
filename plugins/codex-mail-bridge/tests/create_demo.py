"""Create a synthetic offline Thunderbird profile for reproducible review.

All addresses use the reserved .test domain. No real mail or credentials.
"""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import sqlite3


def create_demo(output, attachments=False):
    output = Path(output).resolve()
    home = output / "thunderbird"
    profile = home / "Profiles/demo"
    profile.mkdir(parents=True, exist_ok=True)
    database = profile / "global-messages-db.sqlite"
    if database.exists():
        raise ValueError("Refusing to overwrite an existing demo database.")
    (home / "profiles.ini").write_text("[Profile0]\nName=Review Demo\nIsRelative=1\nPath=Profiles/demo\n", encoding="utf-8")
    prefs = []
    for number, address, host, username, kind in [
        (1, "demo@example.test", "imap.example.test", "demo", "imap"),
        (2, "other@example.test", "imap.example.test", "other", "imap"),
        (3, "pop@example.test", "pop.example.test", "pop", "pop3"),
    ]:
        pairs = {f"mail.identity.id{number}.useremail": address,
                 f"mail.identity.id{number}.fcc_folder": f"{'imap' if kind == 'imap' else 'mailbox'}://{username}@{host}/Sent",
                 f"mail.account.account{number}.identities": f"id{number}",
                 f"mail.account.account{number}.server": f"server{number}",
                 f"mail.server.server{number}.hostname": host,
                 f"mail.server.server{number}.userName": username,
                 f"mail.server.server{number}.type": kind}
        prefs += [f"user_pref({json.dumps(key)}, {json.dumps(value)});" for key, value in pairs.items()]
    (profile / "prefs.js").write_text("\n".join(prefs) + "\n", encoding="utf-8")
    db = sqlite3.connect(database)
    try:
        db.executescript('''
            CREATE TABLE folderLocations(id INTEGER PRIMARY KEY, folderURI TEXT, name TEXT);
            CREATE TABLE messages(id INTEGER PRIMARY KEY, folderID INTEGER, conversationID INTEGER,
                                  date INTEGER, headerMessageID TEXT, deleted INTEGER DEFAULT 0);
            CREATE TABLE messagesText_content(docid INTEGER PRIMARY KEY, c0body TEXT, c1subject TEXT,
                                  c2attachmentNames TEXT, c3author TEXT, c4recipients TEXT);
        ''')
        db.executemany("INSERT INTO folderLocations VALUES (?,?,?)", [
            (1, "imap://demo@imap.example.test/INBOX", "Inbox"),
            (2, "imap://demo@imap.example.test/Sent", "Sent"),
            (3, "imap://other@imap.example.test/INBOX", "Other account"),
            (4, "imap://demo@imap.example.test.evil.test/INBOX", "Wrong host"),
            (5, "mailbox://pop@pop.example.test/Inbox", "POP Inbox"),
        ])
        rows = [
            (101, 1, 10, "2026-10-10T09:00:00", "Project Aurora meeting", "Please confirm the Project Aurora meeting by October 20. 회의 참석을 확인해 주세요.", "alex@example.test", "demo@example.test", "agenda.pdf", 0),
            (102, 2, 10, "2026-10-11T10:00:00", "Re: Project Aurora meeting", "I will confirm after checking our schedule.", "demo@example.test", "alex@example.test", "", 0),
            (103, 1, 11, "2026-10-15T12:00:00", "Weekly update", "The weekly update is ready for review.", "lee@example.test", "demo@example.test", "", 0),
            (201, 3, 10, "2026-10-12T11:00:00", "Other account secret", "This message must never be visible from the demo account.", "other@example.test", "private@example.test", "", 0),
            (202, 4, 10, "2026-10-13T11:00:00", "Wrong-host secret", "Must never be visible.", "evil@example.test", "demo@example.test", "", 0),
            (203, 1, 12, "2026-10-14T12:00:00", "Deleted message", "Must be excluded.", "alex@example.test", "demo@example.test", "", 1),
            (301, 5, 20, "2026-10-15T13:00:00", "POP sample", "POP3 local index is supported.", "alex@example.test", "pop@example.test", "", 0),
        ]
        for mid, fid, tid, date, subject, body, sender, recipient, attachment, deleted in rows:
            timestamp = int(datetime.fromisoformat(date).replace(tzinfo=timezone.utc).timestamp() * 1_000_000)
            db.execute("INSERT INTO messages VALUES (?,?,?,?,?,?)", (mid, fid, tid, timestamp, f"demo-{mid}@example.test", deleted))
            db.execute("INSERT INTO messagesText_content VALUES (?,?,?,?,?,?)", (mid, body, subject, attachment, sender, recipient))
        db.commit()
    finally:
        db.close()
    if attachments:
        from attachment_demo import setup
        setup(profile)
    return {"THUNDERBIRD_HOME": str(home), "THUNDERBIRD_BRIDGE_SETTINGS": str(output / "private-settings.json"),
            "MAIL_BRIDGE_THUNDERBIRD_SETTINGS": str(output / "private-settings.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--attachments", action="store_true", help="Generate synthetic PDF/image originals in a local MIME cache")
    args = parser.parse_args()
    print(json.dumps(create_demo(args.output, attachments=args.attachments), indent=2))
