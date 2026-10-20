# Offline-first desktop app

Version 0 is an offline file-in/file-out engine exposed through a desktop GUI, with the same engine reachable from a headless CLI; real-time streaming is a later milestone. Offline processing is deterministic and unit-testable, which makes it the stable foundation, and the same Chain/Effect code is reused unchanged by the future real-time path. Real-time-first was considered and rejected because device-specific timing bugs and the audio-driver matrix would dominate early development.
