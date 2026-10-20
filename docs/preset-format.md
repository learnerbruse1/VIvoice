# Preset format

Presets are YAML files that describe a named chain of effects.

## Schema

```yaml
name: my-preset            # required, used as the display name
description: optional text # optional
sample_rate: 48000         # optional, must be >= 8000, default 48000
chain:                     # required, non-empty, applied top to bottom
  - type: pitch            # required, matches a registered effect type
    params:                # optional; omitted keys use effect defaults
      semitones: 12
  - type: gain
    params:
      gain_db: -3
```

Rules:

- Unknown `type` values are rejected with the list of registered types.
- A missing `params` key required by the effect is a validation error.
- `vivoice preset validate FILE` checks a file without running it.

## Built-in effects

| type | required params | defaults |
| ---- | --------------- | -------- |
| `gain` | — | `gain_db: 0.0` |
| `pitch` | — | `semitones: 0.0` (range −24…24) |
| `robot` | — | `frequency: 90.0`, `mix: 1.0` |
| `echo` | — | `delay_seconds: 0.2`, `feedback: 0.35`, `mix: 0.5` |
| `voice-conversion` | `model` | `engine: rvc`, `device: auto` |

## Examples

See [`examples/presets/`](../examples/presets/) for ready-to-use presets:
`robot.yaml`, `pitch-up.yaml`, and `deep-voice.yaml`.
