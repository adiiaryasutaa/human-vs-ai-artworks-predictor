"""Model loading and inference for the human-vs-AI art classifier."""

import threading

import numpy as np
from django.conf import settings
from PIL import Image, ImageOps

# Sigmoid output meaning: 1.0 = human, 0.0 = AI.
# Flip to False if predictions look inverted on known images.
HUMAN_IS_ONE = True

# Probabilities inside this band are reported as "Not sure".
# Tune these from the validation ROC curve, not by gut: if false "AI" verdicts
# on human art are the worse error, lower UNCERTAIN_LOW so fewer borderline
# images get called AI.
UNCERTAIN_LOW = 0.4
UNCERTAIN_HIGH = 0.6

# Average the prediction over the image and its horizontal mirror.
# Evaluation uses flip-TTA, so keeping it on here keeps test metrics
# representative of app behavior. Costs a 2-image batch per request.
USE_FLIP_TTA = True

# Reject images whose shorter side is below this (px): the high-frequency
# texture the model relies on is gone, so any verdict would be noise.
MIN_SIDE = 200


class ImageTooSmallError(ValueError):
    """Raised when an input image is below MIN_SIDE on its shorter side."""


_lock = threading.Lock()
_model = None


def get_model():
    """Load the Keras model once, lazily (avoids double-load under the dev autoreloader)."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                import keras

                # Registers the training-only augmentation layers baked into the
                # saved graph so load_model can deserialize them (identity at
                # inference). See detector/aug_layers.py.
                from . import aug_layers  # noqa: F401

                # In deployment the weights live in a Hugging Face model repo;
                # hf_hub_download fetches once and serves from cache thereafter.
                # Locally (no ML_MODEL_REPO), use the on-disk file.
                if settings.ML_MODEL_REPO:
                    from huggingface_hub import hf_hub_download

                    model_path = hf_hub_download(
                        settings.ML_MODEL_REPO, settings.ML_MODEL_FILENAME
                    )
                else:
                    model_path = settings.ML_MODEL_PATH

                _model = keras.models.load_model(model_path)
    return _model


def warm_model_async():
    """Start loading the model in the background if it isn't loaded yet.

    Called when the detector page is opened so the (slow) first model load
    overlaps with the user picking an image. `get_model()` is guarded by
    `_lock` and the `_model is None` double-check, so a concurrent real
    request never triggers a second load.
    """
    if _model is None:
        threading.Thread(target=get_model, daemon=True).start()


def predict_image(image: Image.Image) -> dict:
    """Classify a PIL image. Returns verdict text and class probabilities."""
    model = get_model()
    # input_shape is (None, height, width, channels)
    _, height, width, _ = model.input_shape

    image = ImageOps.exif_transpose(image).convert("RGB")

    w, h = image.size
    if min(w, h) < MIN_SIDE:
        raise ImageTooSmallError(
            f"Image too small ({w}×{h}px). Use artwork at least {MIN_SIDE}px on the shorter side."
        )

    image = image.resize((width, height), Image.Resampling.BILINEAR)

    # EfficientNetV2 has rescaling built in: feed raw [0, 255] pixels.
    array = np.asarray(image, dtype=np.float32)
    if USE_FLIP_TTA:
        batch = np.stack([array, array[:, ::-1, :]])
    else:
        batch = array[None, ...]
    score = float(model.predict(batch, verbose=0)[:, 0].mean())

    p_human = score if HUMAN_IS_ONE else 1.0 - score

    if p_human > UNCERTAIN_HIGH:
        verdict = "Likely Human"
    elif p_human < UNCERTAIN_LOW:
        verdict = "Likely AI"
    else:
        verdict = "Not sure"

    return {
        "verdict": verdict,
        "p_human": p_human,
        "p_ai": 1.0 - p_human,
        "human_pct": round(p_human * 100, 1),
        "ai_pct": round((1.0 - p_human) * 100, 1),
    }
