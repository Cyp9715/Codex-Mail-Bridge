# Development and publication controls

Public source, fixtures, screenshots, commit messages, PRs, issues, logs and review
recordings must use synthetic mail only. Example addresses use `.test`. Keep real
addresses, company identifiers, subjects, bodies, attachment names, credentials,
settings, message/store IDs, local paths and private audit evidence out of releases.
Mail retrieval for an authorized user and publishing development artifacts are
separate actions. Do not send protected addresses or phrases to GitHub search:
download the permitted repository data and compare locally.

## Publication guard

`scripts/publication_guard.py` reads local Git objects and makes no network calls.
It checks the complete staged tree, pending commit messages, and/or all locally
reachable commits and historical blobs, including content deleted from the latest
tree. Private-denylist checks include author and committer headers. Public Git
author addresses are allowed as metadata; messages and source files may contain
only `.test` email examples.

Checks cover mail/settings paths, private work/output directories, personal user
paths, non-test email addresses, credential patterns, symlinks/submodules, oversized
objects needing review, and private protected strings. Findings contain rule names
and opaque object/path digests, never matched text or offending filenames. Common
UTF-16, JSON Unicode, percent-encoded and literal base64 representations of private
strings are checked. This does not detect every possible encoding or all sensitive
content; manually review binary assets and publication text as well.

One exception covers a reviewed public certificate-contact email in the existing
icon's provenance metadata. Both the asset bytes and contact are pinned by hashes;
changed images get no exception. Private-denylist checks are never exempted.

Create a local `private/publication-denylist.json`: a JSON array of protected
addresses, company identifiers and other literal strings. This ignored file is
never packaged. Do not put its contents in a public example, commit, issue or CI.

```sh
git config --local mailbridge.privateDenyFile private/publication-denylist.json
git config --local core.hooksPath .githooks
node scripts/run_publication_guard.cjs --staged --all-history
```

A configured denylist that is missing, unreadable, invalid or empty fails closed.
`MAIL_BRIDGE_PUBLICATION_DENY_FILE` and `--deny-file` support other local locations.
A fresh public clone with no configured list still receives the generic checks.
Hooks use Node.js and find an existing Python 3.10+, including the current user's
bundled Codex runtime or a system installation. `MAIL_BRIDGE_PYTHON` or the local
Git setting `mailbridge.publicationPython` selects one explicitly. No runtime is
downloaded. Configure a working interpreter rather than bypassing failed checks.
Review existing hooks before changing `core.hooksPath`.

- `pre-commit` checks the complete staged tree.
- `commit-msg` checks that tree and the pending commit message.
- `pre-push` checks all locally reachable history, not only the latest tree.

Hooks do not run for GitHub web/API/connector writes. For those workflows, stage the
exact candidate source and write the proposed commit message to an ignored local
file. Run `--staged --all-history --message-file` before uploading blobs or creating
a commit. Verify the uploaded tree matches the checked tree. Update the remote ref
only when its previous SHA still matches the reviewed base, then verify the saved
commit. The ZIP packager also validates all allowlisted inputs with the configured
private denylist before writing an archive.

## Tests and historical audits

```sh
python -m unittest discover -s scripts/tests -p "test_*.py"
python -m unittest discover -s plugins/codex-mail-bridge/tests -p "test_*.py"
python scripts/package.py --output ./outputs
```

Inspect available branches/tags and their full commit graphs, commit messages,
identity headers, historical filenames and blobs. Review repository metadata,
issues, PRs/comments, release assets, Actions runs/artifacts, and available forks.
Keep account-specific results local. Comparisons with an authorized, already-selected
local mailbox must happen in memory without exporting its contents.

A clean audit of accessible history cannot prove a deleted ref, inaccessible
object, cached page, outside clone or transformed fragment never contained private
data. If a leak is found, stop publication, preserve private evidence, tell the owner,
and coordinate removal or credential rotation; never repeat the leaked content in
a public incident discussion.
