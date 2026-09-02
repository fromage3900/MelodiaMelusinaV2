# Lowest-cost art-drop recovery archive

`Tools/artdrop_archive.py` is deliberately local and read-only by default. It
does not invoke AWS, upload, delete, or modify anything under `Content/`.

The allowlist is [`specs/artdrop_archive_manifest.json`](../specs/artdrop_archive_manifest.json).
Only paths listed by `include` are scanned. The tool excludes caches, generated
outputs, marketplace/Fab content, and archive directories, then emits a sorted
SHA-256 manifest.

Preview an archive candidate:

```powershell
python Tools/artdrop_archive.py --manifest specs/artdrop_archive_manifest.json --report "$env:TEMP\artdrop-report.json"
```

An exit code of `2` means an allowlisted include is missing; this is a hold, not
a partial archive. To create a local deterministic gzip tarball, explicitly
provide an output outside `Content/`:

```powershell
python Tools/artdrop_archive.py --manifest specs/artdrop_archive_manifest.json --create "$env:TEMP\artdrop-milestone.tar.gz"
```

Upload, Glacier lifecycle transitions, and deletion remain separate, reviewed
operations. Keep the report beside any future archive and verify every listed
hash after restore before untracking or removing source files.
