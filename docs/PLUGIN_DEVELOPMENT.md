# Developing effects and adapters

This is the extension manual for contributors (human or AI). It assumes you
have run `uv sync --extra dev` and read [docs/ARCHITECTURE.md](ARCHITECTURE.md).

## Add an effect

1. Create `src/vivoice/effects/tremolo.py`:

```python
from typing import ClassVar

import numpy as np

from vivoice.core.effect import Effect, EffectContext


class TremoloEffect(Effect):
    effect_type: ClassVar[str] = "tremolo"
    description: ClassVar[str] = "Amplitude modulation at a low rate."
    default_params: ClassVar[dict] = {"rate_hz": 5.0, "depth": 0.5}

    def process(self, samples: np.ndarray, context: EffectContext) -> np.ndarray:
        t = np.arange(samples.shape[1], dtype=np.float32) / context.sample_rate
        depth = float(self.params["depth"])
        rate = float(self.params["rate_hz"])
        lfo = 1.0 - depth * (0.5 + 0.5 * np.sin(2.0 * np.pi * rate * t))
        return samples * lfo.astype(np.float32)
```

2. Register it by importing the module in `src/vivoice/effects/__init__.py`.
3. Add a unit test in `tests/` that checks output properties, not just "it ran".
4. Document the new `type` in [docs/preset-format.md](preset-format.md).

Rules:

- Keep `process` deterministic: same input and params, same output.
- Never mutate the input buffer; return a new array.
- Put per-effect state on `self`, never in module-level globals.

## Add a voice-conversion engine

Implement `VoiceConversionAdapter` in a new module under `src/vivoice/ai/`,
then register it with `register_adapter`. Follow the RVC adapter in
`src/vivoice/ai/rvc/adapter.py`: lazy imports, a helpful
`MissingDependencyError` when the engine is absent, and engine-native sample
rates declared via `sample_rate`.

Check licensing before vendoring a new engine: a GPL or non-commercial engine
changes what the whole project may link against. Record the decision in
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## Add a GUI page

Add a `QWidget` in `src/vivoice/gui/pages.py` and a nav entry in `gui/app.py`.
GUI pages may read engine state but must not implement DSP or inference.

## Definitions

Use the terms defined in [CONTEXT.md](../CONTEXT.md). If your feature needs a
new concept, add it to the glossary in the same change.
