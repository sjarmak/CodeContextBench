"""
TAC MCP Value Benchmark Adapter.

Provides adapters for TheAgentCompany (TAC) benchmark tasks.
TAC evaluates AI agents on real-world professional tasks.
"""

from benchmarks.ccb_tac.adapter import (
    TACTask,
    TACLoader,
    TACAdapter,
    TAC_ROLES,
    TAC_REGISTRY,
    TAC_VERSION,
)

__all__ = [
    "TACTask",
    "TACLoader",
    "TACAdapter",
    "TAC_ROLES",
    "TAC_REGISTRY",
    "TAC_VERSION",
]
