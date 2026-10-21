# RVC inference via huggingface-hub-rvc

The working default for local RVC inference is the MIT-licensed
`huggingface-hub-rvc` pipeline (`engine: rvc-hub`) rather than the vendored
upstream WebUI in-process (`engine: rvc`). The upstream repo needs fairseq and
PyAV, which do not install reliably on Windows/Python 3.12, while
huggingface-hub-rvc reimplements the RVC architecture (models, rmvpe/fcpe
pitch, retrieval index) without those dependencies and loads classic
RVC-WebUI `.pth`/`.index` character models directly — preserving the community
voice-model ecosystem. First-run inference downloads base assets (hubert,
rmvpe) from `lj1995/VoiceConversionWebUI`; `HF_ENDPOINT` may point at a mirror.
