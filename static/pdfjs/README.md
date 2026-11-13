# PDF.js viewer

Mozilla PDF.js v6.5.438, legacy build, from
https://github.com/mozilla/pdf.js/releases/tag/v6.5.438
(`pdfjs-6.5.438-legacy-dist.zip`). Apache License 2.0; see `LICENSE`.

Removed from the release: source maps (`*.map`), the sample PDF and the
debugger files.

Local changes:

- `program-guide.css` hides the editing and open-file controls.
- `web/viewer.html` has one added `<link>` to that stylesheet.

To upgrade: replace `build/` and `web/` from a newer legacy release, remove
the same extras, and re-add the `<link>` line in `web/viewer.html`.
