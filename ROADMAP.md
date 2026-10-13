# Roadmap: ideas saved for later

Not built yet, on purpose. Each needs a decision from the user first.

## For distribution (when documents are shared as a set)

- **Series on covers:** list the other documents of the same course on the back of the cover and on the back
  cover, each with a link, and mark "you are here". Designed in the October 2026 mock-up and set aside until
  documents are distributed together.
- **QR codes:** a QR code per document on the back cover, pointing at the latest PDF online (the `qrcode`
  package is available in TeX Live and MikTeX). Useful on printed copies.
- **Pack cover per audience:** a pack label and blurb per course or exam, from a small series file.

## Covers and pages

- **Bangla back-of-cover pages:** the pages are English for a `lang: bn` document; give each its Bangla text.
- **Cover gallery:** `doc.py gallery` building every type's cover from its template into one PDF, for choosing.
- **Front-matter for the project-report table:** submitted by / submitted to / ID fields on its cover.

## Interactive PDF (needs Acrobat, so left out while the browser is the main reader)

- Hide-and-reveal answers on self-checks (optional content groups).
- Revision checkboxes that keep their state.
- "Back to where I was" buttons.
