# Mail Bridge review walkthrough and evidence

Version 0.4.0 · Cyp Soft · synthetic public demonstrations only

One stdio MCP server exposes 19 tools. The manifest contains twelve positive cases
(six Thunderbird, six classic Outlook) and three negative cases. Natural-language
routing and visible host behavior require a real walkthrough; unit tests alone
do not mark those review cases passed.

## Evidence collected

- Automated tests: Thunderbird account boundaries, shared conversations,
  read-only database access, UTC filters, Unicode/literal queries, pagination,
  account-choice storage/legacy fallback, and relocated per-OS profile discovery.
- Automated Outlook tests: explicit selection, private portable settings,
  unsupported shared-store layout, invalid settings, literal search and partial
  reporting, scoped conversation requests, dates, input validation, runtime
  discovery, sanitized security/timeout errors, and synthetic COM scope checks.
- Live Windows Office Standard 2019 x64: account discovery/selection, status,
  bounded search, body reading, conversation reading passed on one IMAP account.
  A separate read test preserved the sampled message's unread state.
- Attachment evidence: generated PDF/PNG/duplicate-name MIME, metadata-only
  search, no body-column reads, listing without payload decoding, byte/hash equality,
  typed image opt-out, mbox/maildir/custom paths, scope/change/protection limits,
  temporary-copy cleanup and stdio handoff pass automated tests. Outlook attachment
  access uses synthetic COM properties; live provider/installed-host attachment
  workflows and file analysis remain unverified.
- Other PCs/Office editions: not run. macOS/Linux live Thunderbird: not run.
- Public host review prompts, negative routing, recording and playback: not run.

The live test used authorized local data, which is absent from this package,
report, public screenshots, and demo materials. Synthetic tests are not presented
as a real Outlook profile, Office-wide certification, or a recorded demo.

## Isolated Thunderbird demo

1. Run `tests/create_demo.py --output <new-temporary-folder> --attachments`.
2. Use its printed environment variables in a dedicated development connection.
   Do not change the normal mailbox's settings or use a production chat.
3. Discover Review Demo and explicitly select `demo@example.test`.
4. Check status: three indexed messages, latest 2026-10-15 12:00 UTC.
5. Find Project Aurora from Alex, read the meeting deadline, and show its thread.
6. Search attachment metadata for subject Aurora and filename agenda, list message
   101, then get one agenda.pdf by its opaque ID. Compare original bytes/hash;
   list/get diagram.png to verify typed image display. No document parser is used.
   The two agenda.pdf parts have distinct IDs. Do not transfer both implicitly.

## Isolated Outlook demo

Use a dedicated classic Outlook test profile/account and unique delivery store.
Prepare only `.test` sample addresses and fictional Project Aurora mail, including
the October 20 confirmation request and a reply in the same conversation. The
Thunderbird fixture is not an Outlook PST; do not pretend it is a COM result.
Opening/changing Outlook profiles and importing sample mail are reviewer setup,
not bridge tools. Never import samples into the user's production mailbox.

In a dedicated local development chat, discover the test account, explicitly
select it, check status, search October Project Aurora from Alex, read the returned
message ID, and follow its actual conversation ID. Add only generated PDF/image
attachments in the isolated reviewer setup. Search metadata, list the one mail,
get only the requested original, compare bytes and test actual host file access.
A synthetic COM test is not proof of live provider attachment support. Verify unread state remains
unchanged. Show `scan_incomplete` when using a small scan limit. Use the exact
server/skill version being packaged and actual returned data.

## Record and verify

Record readable host prompts and results for both clients, then a request to
send/delete or execute an attachment. The host must explain those unsupported
actions without calling mail tools or claiming success. Include metadata-first
original-file handoff and typed image display in the positive cases. Screen control is not video recording;
use an actual recorder. No fabricated results may stand in for real host workflows.

Play the saved video back and inspect readability, case coverage, and absence
of real addresses, account paths, production mail, unrelated chats, credentials,
or notifications. Host the actual recording at a reviewer-accessible URL and
verify unauthenticated playback before writing `review.demo_recording_url`.
Rebuild the ZIP after adding verified evidence. The recording is still incomplete.

## Public submission state

Publisher Cyp Soft, free/no commerce, all available countries, independent icon,
English base/Korean listing, and public policy/support pages are prepared. Confirm
the actual repository URLs before submission. Developer verification and local
MCP organization allowlisting remain external requirements. See
https://developers.openai.com/plugins/deploy/desktop-only and docs/SUBMISSION.md.
No public submission, approval, or publication is claimed by this bundle.

The existing private account registration retains its immutable original package
name. Public/local source uses `codex-mail-bridge`; audience remains private until
the separate OpenAI review/publication process succeeds.
