# Thunderbird Bridge · Cyp Soft

This package contains a local desktop MCP server and workflow skill for one
explicitly selected Thunderbird IMAP/POP3 account. It is independent of Mozilla
and Thunderbird. The code is MIT licensed.

Node.js 18+ and Python 3.10+ are required. The launcher uses an existing Codex
bundled Python when available, then tries installed Python. Nothing is downloaded.
Set `THUNDERBIRD_PYTHON` to an executable if needed.

After installing, ask the AI to discover your Thunderbird profiles and accounts.
Choose one account explicitly. Use the status, search, read, and thread tools.
Only selected-account indexed mail is accessible. Account metadata and retrieved
mail are sent to the AI host as tool results; no publisher backend or telemetry
is included. Global Search and Indexer must be enabled in Thunderbird.

Search date filters and timestamps are UTC. The index can be stale or incomplete.
Sending, deletion, draft saving, read-status changes, and attachment contents are
not supported. Windows has been tested; other OS discovery paths need validation.

Private settings live under the current user's CypSoft/ThunderbirdBridge
application-settings directory, outside this package. Do not copy them into a
release. `THUNDERBIRD_HOME` and `THUNDERBIRD_BRIDGE_SETTINGS` isolate synthetic
review environments. See `tests/create_demo.py` and `docs/REVIEW.md`.

If the current settings file is absent, the bridge can read an existing 0.1.x
selection from the previous CypSoft/ThunderbirdMailBridge directory. Read-only
calls never move or modify settings. A new explicit selection uses the new
directory. Delete both selection files to forget the account entirely.

Source, policies, and support are published at https://github.com/Cyp9715/Thunderbird-Bridge.
Public local-MCP directory submission separately requires eligibility, publisher
verification, a real host demo, and review. This is not an approved listing.

Thunderbird is a trademark of the Mozilla Foundation in the U.S. and other countries.
See THIRD_PARTY_NOTICES.md. No official affiliation or endorsement is claimed.
