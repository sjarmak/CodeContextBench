"""Gemini driver agent stub for CodeContextBench multi-harness evaluation.

Import path (matches harness_registry.json):
    agents.gemini_driver_agent:GeminiDriverAgent
"""


class GeminiDriverAgent:
    """Stub agent for Gemini harness.

    Implement by subclassing the appropriate Harbor agent base class
    and adding Gemini CLI invocation logic.
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "GeminiDriverAgent is a stub. Implement Gemini harness integration "
            "before using this agent."
        )
