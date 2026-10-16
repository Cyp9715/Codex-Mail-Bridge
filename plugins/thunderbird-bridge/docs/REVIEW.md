# Review walkthrough and evidence

Version 0.2.0 · synthetic fixtures only

The manifest contains five positive and three negative cases. Positive behaviors
have automated tool-level coverage in `tests/test_bridge.py`. Natural-language
model routing and the negative prompts' user-visible responses require a real
host walkthrough; they are not claimed as passed by unit tests.

## Prepare an isolated demo

1. Generate fake data with `tests/create_demo.py --output <new-temporary-folder>`.
2. Launch the local server in a dedicated development connection with the two
   printed environment variables. Do not change the normal mailbox's settings.
3. Discover the Review Demo profile and explicitly select `demo@example.test`.
4. Check status: three indexed messages; latest 2026-10-15 12:00 UTC.

All fixture addresses are reserved `.test` domains. Another account and a
lookalike host are included specifically to test account-boundary enforcement.
No reviewer credentials or production data belong in the ZIP.

## Record in the desktop host

Record the installed plugin name/version and the following actual interactions.
Keep the prompts/results readable for a few seconds each.

1. “Check my selected Thunderbird account and the latest indexed message date.”
2. “Find Project Aurora mail from alex@example.test in October 2026.”
3. “Read the meeting email. When do I need to confirm?”
4. “Show the Project Aurora conversation.”
5. “Send Alex my approval.” The host must explain that sending is unavailable.

Expected results are in `plugin.json`. Never replace real tool results with
mockups or claim a typed script is a recorded demo. Use a clean window and keep
unrelated chat history, notifications, paths, tokens, and production mail out of
the frame. Screen control alone does not record video; use an actual recorder.

Play back the recording and inspect prompts, results, privacy, and coverage.
Host the actual recording at a reviewer-accessible URL, verify playback without
private sign-in, and only then set `review.demo_recording_url` and rebuild the ZIP.

## Public submission prerequisites

The listing uses Cyp Soft, free/no commerce, all available countries, and an
English base listing with Korean translation. Publisher verification is not
claimed. Website, support, privacy, and terms URLs point to the public project repository.
Verify their contents and access before a portal submission. A recorded host demo
and developer verification remain separate requirements.

Local MCP submissions currently require approved-partner/organization access.
See https://developers.openai.com/plugins/deploy/desktop-only. Confirm eligibility
before the portal submission step. Upload, review submission, and publication
are separate actions. No public submission or publication is performed by this
source package.

The local installation identifier is thunderbird-bridge. The displayed
name is Thunderbird Bridge. The maintainer selected this name; notices do not
constitute trademark permission or a legal clearance.
