"""Identity stand-ins for the training-only augmentation layers baked into the
saved model graph.

`best_model4.keras` was saved with custom augmentation layers
(`RandomJPEGQuality`, `RandomDownscale`, `RandomGaussianNoise`, `RandomCutout`)
registered under the `aug>` package. They only do anything during training; at
inference they are pass-through. Keras still refuses to deserialize the model
unless their classes are importable and registered, so we re-declare them here
as identity layers. Importing this module runs the
`@register_keras_serializable` decorators, which is all `load_model` needs.

Rebuilding a stripped inference artifact (no augmentation block) or exporting to
ONNX would remove this dependency entirely — see the project brief.
"""

import keras

# Base Layer kwargs we forward to super(); everything else in a saved config is
# an augmentation hyperparameter we keep only so get_config() round-trips.
_BASE_KWARGS = ("name", "trainable", "dtype", "dynamic")


class _IdentityAug(keras.layers.Layer):
    """Pass-through layer that accepts and preserves any saved config kwargs."""

    def __init__(self, **kwargs):
        base = {k: kwargs[k] for k in _BASE_KWARGS if k in kwargs}
        super().__init__(**base)
        self._aug_config = {k: v for k, v in kwargs.items() if k not in _BASE_KWARGS}

    def call(self, inputs, training=None):
        return inputs

    def get_config(self):
        return {**super().get_config(), **self._aug_config}


@keras.saving.register_keras_serializable(package="aug")
class RandomJPEGQuality(_IdentityAug):
    pass


@keras.saving.register_keras_serializable(package="aug")
class RandomDownscale(_IdentityAug):
    pass


@keras.saving.register_keras_serializable(package="aug")
class RandomGaussianNoise(_IdentityAug):
    pass


@keras.saving.register_keras_serializable(package="aug")
class RandomCutout(_IdentityAug):
    pass
