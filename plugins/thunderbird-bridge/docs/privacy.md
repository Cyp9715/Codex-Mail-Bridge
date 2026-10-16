# Privacy notice

**Thunderbird Bridge · Cyp Soft · effective October 16, 2026**

## Local data access

The bridge discovers registered Thunderbird profiles, reads limited account
identity/server preferences, and queries the local global search index. You
explicitly select one account before mail can be queried.

Discovery can return profile names, email addresses, and server metadata to the
AI host. Selected-account results can contain folder names, dates, subjects,
senders, recipients, Message-ID headers, indexed body text, and attachment names.
Password stores and attachment contents are not read.

## Storage and network behavior

The bridge saves profile/account IDs and an identity fingerprint in per-user
application settings outside the plugin. It does not save another copy of email
or modify Thunderbird's mailbox/index. The selection file contains no passwords,
mail text, account addresses, or absolute profile paths.

The stdio server makes no network calls and includes no publisher backend,
analytics, tracking, advertising, or payments. The launcher uses installed
software and downloads nothing.

## AI host

Local execution does **not** make this an offline AI service. Retrieved metadata
and email text are returned to the AI host that invoked the tool. That host
processes results under its own settings and policies, including storage and
retention. Cyp Soft's bridge cannot control or delete the host's chat history.
Check host policies and your authorization before using confidential/company mail.

## GitHub and voluntary support

GitHub hosts the project and applies its own policies to visits and interactions.
If you post an issue, its contents are public and visible to maintainers and other
users. Do not include private mail, credentials, or account settings. This plugin
has no separate support-data collection or retention backend.

## Stop access

Disable/uninstall the plugin to stop its tools. Delete its local selection file
to forget the account choice. This does not delete Thunderbird mail or AI-host
conversation history. Use each host's own controls for those records.
See the [README](../README.md) for settings locations.

For privacy questions, use the [support page](support.md), without disclosing
private information in public issues.
