# Compare selected original files

1. Search the selected Thunderbird account's mail/attachment metadata by topic, parties, dates and filename. Union
   spelling variants and follow pages before retrieving files. For a known mail
   ID, list its attachments directly. A missing filename match does not establish
   absence: indexed metadata can be incomplete or the file can be in a container.
2. Build a provenance table: Thunderbird account, message ID, sender, indexed mail
   timestamp, original filename, attachment ID, original byte count and SHA-256.
   The same name may have different bytes; different names may be duplicates.
   Document-internal dates, filenames and delivery dates are distinct evidence.
   A later delivery is not necessarily a later revision or a signed final copy.
3. Get only candidate originals needed for the comparison, sequentially in small
   batches. Receipt metadata links the original to its message. Verify the local
   file and hash, then open it using the host's authorized file/image tools.
   A local_path response alone does not mean GPT has read or uploaded the file.
4. The bridge does not parse PDF/Office documents, OCR, unzip or expand TNEF.
   If format_hint is tnef, winmail.dat can contain the real document. An available
   host decoder may inspect and extract just needed members locally as data;
   preserve outer/inner hashes and names. Apply size/count limits and reject
   traversal, links and executable members. Never run an attachment or fetch
   external document links/images. If a required decoder or original is absent,
   report what remains unread instead of claiming there was no attachment.
5. For DOCX, use the host's document tools to inspect body, tables, notes and
   relevant headers/footers. Check tracked insertions/deletions, ordinary
   strikethrough/double-strikethrough, comments and colored amendments; plain text
   extraction can concatenate deleted and replacement language into a false
   clause. Distinguish visible edit proposals from accepted wording and verify
   material ambiguous formatting visually when possible. For scanned PDFs or
   images, OCR/vision is a host capability and must actually succeed before claims.
6. Compare clauses/sections across adjacent versions and then summarize the latest
   confirmed document. Separate substantive changes, formatting/typos, unchanged
   terms and unknown annexes. Do not infer rights, acceptance, signatures or payment
   from an email proposal. Cite the document/version and specific clause for each
   material difference; the host chooses its supported source citation format.

Exports are temporary: later get/cleanup removes files older than 10 minutes;
at most 16 remain. For longer authorized analysis, first retain a verified copy
under an ignored private task directory, record provenance/hash, and release the
managed export. This private host copy is outside bridge cleanup; remove it when
no longer needed, without implying local cleanup recalls copies already in chat.
Never copy source documents, filenames, clauses or comparison reports into a
public repository, release, issue, commit, diagnostic comment or example.
