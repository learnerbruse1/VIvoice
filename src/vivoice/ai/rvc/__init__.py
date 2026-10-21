"""RVC voice-conversion adapters (in-process and HTTP)."""

from vivoice.ai.rvc.adapter import RVCAdapter
from vivoice.ai.rvc.http import RvcHttpAdapter

__all__ = ["RVCAdapter", "RvcHttpAdapter"]
