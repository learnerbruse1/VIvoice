# VIvoice

A voice changer framework: deterministic DSP effects plus pluggable AI voice conversion, offline-first with a real-time milestone. This file is the project glossary and nothing else.

## Language

### Effects and pipeline

**Effect**:
A deterministic DSP transformation applied to an audio stream, such as pitch shift, formant shift, or reverb.
_Avoid_: audio filter, DSP module

**Chain**:
The ordered sequence of Effects that processes one stream of audio.
_Avoid_: pipeline, effect stack, audio graph

**Stream**:
The real-time, block-wise processing path that reuses the same Chain and Effect
classes as offline rendering, holding state across blocks instead of resetting.
_Avoid_: live mode, realtime mode

**Preset**:
A saved YAML document that names a Chain and the parameter values for every Effect in it.
_Avoid_: profile, configuration, patch

### Voice conversion

**Voice Conversion**:
An AI-based transformation that changes the speaker identity (timbre) while preserving the spoken content.
_Avoid_: voice cloning, timbre swap, 变声 (overloaded)

**Voice Model**:
An importable model package, a `.pth` checkpoint with an optional `.index`, that represents one character voice.
_Avoid_: voice pack, timbre file

**Voice Conversion Adapter**:
The pluggable boundary that binds a voice-conversion engine (RVC by default) into a Chain.
_Avoid_: backend, driver, engine

**Reference Audio**:
A short recording used to derive a new voice without training a model; zero-shot conversion is planned behind the same adapter.
_Avoid_: sample clip, target voice
