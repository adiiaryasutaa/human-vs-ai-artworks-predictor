# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Rules

- **No hallucinations.** Do not invent APIs, functions, or features. Only reference what exists in actual project files or verified docs.
- **Clarify ambiguity.** Ask before assuming. Prefer asking many questions over guessing wrong.
- **Best practices.** Follow framework-specific best practices: React 19, TypeScript, Express 5, Tailwind CSS, Supabase JS SDK.

## Commands

```bash
# Setup (Python 3.12 required — Keras ≥ 3.11 dropped 3.9)
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run dev server
.venv/bin/python manage.py runserver

# Run tests
.venv/bin/python manage.py test
```

No migrations needed — `DATABASES = {}`.

## Architecture

Single-page Django app: one view, one template, no DB, no auth.

**Request flow:**
1. `detector/views.py:index` — accepts POST with `artwork` (file upload) or `image_url` (string)
2. URL inputs go through `detector/urlfetch.py:fetch_image_bytes` — has SSRF guards (scheme check, public-IP-only DNS validation, redirect re-validation)
3. PIL Image passed to `detector/ml.py:predict_image` — preprocesses, runs inference, returns verdict dict
4. Result rendered in `detector/templates/detector/index.html` (Flowbite/Tailwind via CDN)

**ML layer (`detector/ml.py`):**
- Model loaded lazily via thread-safe singleton (`get_model()`) — avoids double-load under Django's autoreloader
- Active model: `models/best_model2.keras` (set in `config/settings.py:ML_MODEL_PATH`)
- Input size read from model at startup — no hardcoding
- EfficientNetV2 has rescaling built in; feed raw `[0, 255]` pixels (no manual normalization)
- `USE_FLIP_TTA = True` — averages prediction over image and its horizontal mirror (matches training evaluation)
- `HUMAN_IS_ONE = True` — flip if predictions are inverted on known images
- Uncertainty band: `UNCERTAIN_LOW=0.4` / `UNCERTAIN_HIGH=0.6` — tune from validation ROC, not gut

**Key tuning constants in `detector/ml.py`:**
- `HUMAN_IS_ONE` — whether sigmoid output 1.0 means human
- `UNCERTAIN_LOW` / `UNCERTAIN_HIGH` — verdict threshold band
- `USE_FLIP_TTA` — test-time augmentation toggle

**Switching models:** change `ML_MODEL_PATH` in `config/settings.py`. Three `.keras` files exist in `models/`.
