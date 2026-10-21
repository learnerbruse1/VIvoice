"""RVC voice-conversion adapters (in-process and HTTP)."""

from vivoice.ai.rvc.adapter import RVCAdapter
from vivoice.ai.rvc.http import RvcHttpAdapter
from vivoice.ai.rvc.hub import RvcHubAdapter

__all__ = ["RVCAdapter", "RvcHttpAdapter", "RvcHubAdapter"]
