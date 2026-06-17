# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django web app that estimates whether **artwork** (paintings, drawings, digital art — not photos/screenshots) is human-made or AI-generated, using an EfficientNetV2 Keras model. Server-rendered, no DB, no auth, no build step.

## Rules

- **No hallucinations.** Do not invent APIs, functions, or features. Only reference what exists in project files or verified docs.
- **Clarify ambiguity.** Ask before assuming. Prefer asking many questions over guessing wrong.
- **Stack & conventions.** Python 3.12 / Django 5; Pillow + Keras for ML; vanilla JS (no framework); Tailwind + Flowbite via CDN (no bundler). Match the editorial design tokens in `base.html` (colors `paper/ink/ash/line/human/ai`; fonts Newsreader / Inter / IBM Plex Mono; hard corners, hairline rules).

## Commands

```bash
# Setup (Python 3.12 required — Keras ≥ 3.11 dropped 3.9/3.10)
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run dev server
.venv/bin/python manage.py runserver

# System check / tests (no tests defined yet)
.venv/bin/python manage.py check
.venv/bin/python manage.py test
```

No migrations — `DATABASES = {}`. Model weights (`.keras`) are **gitignored**; place one in `models/` and point `ML_MODEL_PATH` at it (`config/settings.py`, default `models/best_model2.keras`).

## Architecture

Two routes, a shared base template, no DB/auth.

**Routes (`detector/urls.py`):**
- `/` → `views.landing` → `landing.html` (hero, how-it-works, about, FAQ)
- `/detect/` → `views.detect` → the detector tool

**Request flow (`/detect/`):**
1. `views.detect` — POST with `artwork` (file upload) or `image_url` (string). GET warms the model and lists examples.
2. URL inputs → `detector/urlfetch.py:fetch_image_bytes` — SSRF guards (scheme check, public-IP-only DNS validation, redirect re-validation, 15 MB cap).
3. PIL image → `detector/ml.py:predict_image` — preprocess, infer, return verdict dict (`verdict`, `p_human`, `p_ai`, `human_pct`, `ai_pct`).
4. AJAX requests (`X-Requested-With: XMLHttpRequest`) get the `_result.html` partial; a plain POST re-renders `index.html`. Templates: `base.html` (shell) ← `index.html` / `landing.html`; `_result.html` is the verdict fragment, included by `index.html` and returned alone for AJAX.

**Frontend (no framework, no build):**
- Progressive enhancement: forms work as a full POST; JS upgrades to `fetch` → injects `_result.html` into `#result`, shows the analyzed image + spinner, auto-scrolls.
- Inputs: file upload, URL, clipboard paste, camera. Client-side validation mirrors server caps (PNG/JPG/WEBP, 15 MB).
- Examples: drop images into `detector/static/detector/examples/`; the "try one" row auto-shows (scanned by `views.py:_example_images`).

**ML layer (`detector/ml.py`):**
- `get_model()` — thread-safe lazy singleton (avoids double-load under the autoreloader); `warm_model_async()` preloads it in a daemon thread on `/detect/` GET so the first inference isn't a cold start.
- Input size is read from the model at startup — no hardcoding.
- EfficientNetV2 has rescaling built in; feed raw `[0, 255]` pixels (no manual normalization).
- Uncertainty band `UNCERTAIN_LOW=0.4` / `UNCERTAIN_HIGH=0.6` → "Not sure"; tune from validation ROC, not gut.

**Key tuning constants (`detector/ml.py`):**
- `HUMAN_IS_ONE` — whether sigmoid output 1.0 means human (currently `False`); flip if verdicts are inverted on known artwork.
- `UNCERTAIN_LOW` / `UNCERTAIN_HIGH` — verdict threshold band.
- `USE_FLIP_TTA` — average prediction over image + horizontal mirror (matches training eval).

## Gotchas

- **Tailwind Play CDN + custom config is incompatible with SRI.** Do NOT put `integrity`/`crossorigin` on the `cdn.tailwindcss.com` script in `base.html` — it silently kills the runtime JIT, so `tailwind.config` (custom colors/fonts) and the `@apply` component layer stop applying and the page renders unstyled. Flowbite's static CSS SRI is fine. (Play CDN is dev-grade; a Node build step would fix both, but this project avoids Node.)
- **`index.html` inline JS: keep the initial `activateTab()` call LAST in the script.** It runs `stopCamera()`, which reads camera `const`s (`stream`, `video`, …) declared further down — calling it earlier throws a temporal-dead-zone `ReferenceError` that aborts the entire script and silently breaks the preview, async submit, paste, and examples.

## Switching models

Change `ML_MODEL_PATH` in `config/settings.py`. Several `.keras` files may exist locally in `models/` (gitignored — not in the repo).
