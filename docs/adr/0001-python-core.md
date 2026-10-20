# Python for the core engine

The audio core is written in Python (3.11–3.13, default 3.12) instead of Rust or C++. The AI voice-conversion features live in the Python/PyTorch ecosystem, so a Python core avoids a two-language split, and future contributors are expected to be AI agents that work most fluently in Python; latency targets hold because heavy inference runs off the audio callback thread. Considered and rejected: Rust with cpal/fundsp/rubato (strong real-time story but forces a Python sidecar for AI) and C++ with iPlug2/JUCE (plugin focus plus AGPL/commercial licensing concerns).
