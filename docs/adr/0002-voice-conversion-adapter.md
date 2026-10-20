# Adapter-based voice conversion

Voice conversion is an adapter boundary rather than an integrated engine. The default adapter wraps RVC-Project/Retrieval-based-Voice-Conversion-WebUI (MIT) so community `.pth`/`.index` character models from HuggingFace, voice-models.com, and similar sites can be imported directly. Seed-VC (GPL-3.0, repo archived) and Applio (MIT non-commercial) are excluded from default integration for license cleanliness, and zero-shot reference-audio conversion (OpenVoice, Seed-VC) is deferred behind the same interface.
