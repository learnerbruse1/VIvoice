# third_party

This directory holds vendored third-party sources. Vendored content is
git-ignored so the repository stays small and license-clean; only this README is
committed.

## RVC engine

The default AI voice-conversion engine is the official, MIT-licensed
[RVC-Project/Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI).

Fetch it at a pinned ref with:

```bash
python scripts/fetch_rvc.py --ref main
```

The script records the exact commit in `third_party/RVC_COMMIT.txt`. Do not
commit the sources or the pin file to git; pin files for releases are tracked
through the script invocation in your build/CI configuration instead.

If you vendor another component, keep a copy of its license inside its
directory and list it in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
