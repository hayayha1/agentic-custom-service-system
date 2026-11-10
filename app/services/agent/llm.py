"""OpenAI-compatible native tool calling; never parse prose as executable JSON."""
import json
import httpx

from app.core.config import settings
from app.services.model_service import model_service


class NativeToolClient:
    def __init__(self, model=None):
        self.model = model

    @property
    def model_name(self):
        return self.model or model_service.llm_model

    @property
    def enabled(self):
        key = model_service.llm_api_key or ""
        return bool(key and not key.startswith("your_") and key != "test")

    async def call(self, messages, tools, force=None):
        if not self.enabled:
            return None
        payload = {"model": self.model_name, "messages": messages, "tools": tools,
                   "temperature": 0, "parallel_tool_calls": False,
                   "tool_choice": {"type": "function", "function": {"name": force}} if force else "required"}
        async with httpx.AsyncClient(timeout=min(20, settings.AGENT_TIMEOUT_SECONDS)) as client:
            response = await client.post(
                f"{model_service.llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {model_service.llm_api_key}"}, json=payload)
            response.raise_for_status()
        result = response.json()
        calls = result["choices"][0]["message"].get("tool_calls", [])
        if len(calls) != 1:
            raise ValueError("Expected exactly one native function call")
        call = calls[0]
        if call["function"]["name"] not in {t["function"]["name"] for t in tools}:
            raise ValueError("Unknown native tool call")
        args = json.loads(call["function"]["arguments"])
        if not isinstance(args, dict):
            raise ValueError("Function arguments must be an object")
        return {"name": call["function"]["name"], "arguments": args,
                "id": call.get("id", "call_agent"), "usage": result.get("usage", {})}


native_client = NativeToolClient()
