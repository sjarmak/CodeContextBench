"""Cursor driver agent stub for CodeContextBench multi-harness evaluation.

Import path (matches harness_registry.json):
    agents.cursor_driver_agent:CursorDriverAgent
"""


class CursorDriverAgent:
    """Stub agent for Cursor harness.

    Implement by subclassing the appropriate Harbor agent base class
    and adding Cursor CLI invocation logic.
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "CursorDriverAgent is a stub. Implement Cursor harness integration "
            "before using this agent."
        )
