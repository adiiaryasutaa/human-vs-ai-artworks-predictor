# Example images

Drop a few image files here and the **"No image? Try one"** row on `/detect`
turns on automatically (it stays hidden while this folder has no images).

- Accepted: `.png`, `.jpg`, `.jpeg`, `.webp`
- Shown sorted by filename; labelled neutrally as "Example 1", "Example 2", …
  (no human/AI ground truth is asserted in the UI).
- A good set: a couple of clearly human-made works and a couple of obviously
  AI-generated ones, so first-time visitors can see both verdicts.

Suggested names: `example-1.jpg`, `example-2.jpg`, `example-3.jpg`, `example-4.jpg`.

The detector view scans this directory via Django's staticfiles finder
(`detector/views.py:_example_images`), so no code change is needed when you
add or remove files — just restart the dev server if it doesn't pick them up.
