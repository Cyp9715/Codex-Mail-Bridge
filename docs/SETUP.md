# Thunderbird installation and account setup

Run `thunderbird_diagnostics` before mail access in a new session. It checks local
executable registrations, registered profiles, supported account counts and index
presence. It does not start Thunderbird, open the mail database, authenticate to a
server or return account identities, profile paths or message content.

| Result code / condition | Explain to the user and next action |
| --- | --- |
| `thunderbird_not_detected` | No supported installation or usable profile was detected. Install Thunderbird, open it and add the intended existing mail account. A portable/custom installation may instead need its profile registry made discoverable. |
| `thunderbird_profile_unconfirmed` | Installation evidence exists or is inconclusive, but no usable registered profile was confirmed. Open Thunderbird to complete setup; check the configured profile registry and permissions. |
| `account_registration_unconfirmed` | No supported local IMAP/POP3 account was confirmed. Add or complete that account in Thunderbird. If configuration was unreadable, check profile access rather than claiming there are no accounts. |
| `thunderbird_index_missing` | Account configuration exists but an index is missing. Enable Global Search and Indexer, sync needed mail and let indexing finish. |
| `selection_required` | Discover profiles/accounts and ask for an explicit account choice before selection. Never choose an account automatically. |
| `selection_saved` | Run `thunderbird_status` to validate the saved account. A saved selection alone does not prove current availability. |

Unreadable or malformed registries and unavailable profile paths take precedence over
installation guidance: check configuration and access before reinstalling.

After the user finishes the relevant setup step, run diagnostics again. Explain
the returned `guidance` in the user's language. Do not loop over startup commands,
collect passwords, change security policy or silently switch profiles/accounts.
The bridge does not register accounts or log in on the user's behalf.

Executable detection checks PATH, Windows App Paths and standard install locations,
macOS application bundles, and common Linux Snap/Flatpak executable locations.
An undetected executable does not prove Thunderbird was uninstalled. Existing
registered profiles and usable caches remain supported even when the application
is closed or a portable executable is outside those locations.

Account counts describe recognized local IMAP/POP3 configuration only. They do not
verify a password, live sign-in, server availability or completed synchronization.
Unsupported/partial account configuration and unreadable preferences are reported
as unconfirmed rather than silently treated as authenticated accounts.

Official setup references:

- [Download Thunderbird](https://www.thunderbird.net/en-US/download/)
- [Get started and add an account](https://support.mozilla.org/en-US/kb/getting-started-thunderbird)
- [Manual account configuration](https://support.mozilla.org/en-US/kb/manual-account-configuration)
- [Global Search and Indexer](https://support.mozilla.org/en-US/kb/global-search)

See [CLI](CLI.md), [compatibility](THUNDERBIRD_COMPATIBILITY.md) and [privacy](privacy.md).
