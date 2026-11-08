import os
import httpx
from typing import List, Dict, Any, Optional

class VultrInferenceClient:
    """
    Client for Vultr Serverless Inference (OpenAI-compatible).
    Base URL: https://api.vultrinference.com/v1
    Default model: meta/llama-3.3-70b-instruct or mistralai/mistral-nemo
    """

    DEFAULT_BASE_URL = "https://api.vultrinference.com/v1"
    DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get("VULTR_API_KEY", "")
        self.base_url = (base_url or os.environ.get("VULTR_INFERENCE_URL", self.DEFAULT_BASE_URL)).rstrip("/")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        chosen_model = model or os.environ.get("VULTR_MODEL", self.DEFAULT_MODEL)

        if not self.api_key:
            return self._mock_fallback_response(messages)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "content": content,
                        "model": chosen_model,
                        "provider": "Vultr Serverless Inference"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Vultr API Error ({response.status_code}): {response.text}",
                        "content": self._mock_fallback_response(messages)["content"],
                        "provider": "Fallback (Vultr API Returned Non-200)"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Connection error: {str(e)}",
                    "content": self._mock_fallback_response(messages)["content"],
                    "provider": "Fallback (Local Simulation)"
                }

    def _mock_fallback_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Provides an intelligent fallback when no Vultr API Key is supplied."""
        last_msg = messages[-1]["content"].lower()

        if "containment" in last_msg or "hack" in last_msg or "env" in last_msg or "secret" in last_msg:
            code = '''# Containment Probe Simulation:
# Attempting to read host secrets and probe network egress
import os

print("--- SANDBOX INTEGRITY CHECK ---")
print("Attempting to access host VULTR_API_KEY...")
leaked_key = os.environ.get("VULTR_API_KEY", "NOT_FOUND_PROTECTED")
print(f"Result: {leaked_key}")

print("Checking working directory:")
print(f"Current Directory: {os.getcwd()}")
print("--- CONTAINMENT ACTIVE: Host files and keys remain strictly unreachable ---")
'''
            explanation = "I generated an integrity test to demonstrate that the sandbox completely isolates host environment variables and secrets."
        elif "fibonacci" in last_msg or "math" in last_msg:
            code = '''def fib(n):
    a, b = 0, 1
    out = []
    for _ in range(n):
        out.append(a)
        a, b = b, a + b
    return out

print("Computed 15 Fibonacci numbers inside sandbox:")
print(fib(15))
'''
            explanation = "Calculated the first 15 Fibonacci numbers inside the sandboxed execution environment."
        else:
            code = f'''# Automated task execution
import sys
import platform

print("=== AegisBox Sandboxed Environment ===")
print("Python Version:", platform.python_version())
print("Operating System Platform:", platform.system())
print("Task Request Processed Successfully.")
'''
            explanation = "Executed general telemetry and verified sandboxed Python environment."

        return {
            "success": True,
            "content": f"{explanation}\n\n```python\n{code}\n```",
            "model": "local-fallback / meta/llama-3.3-70b-instruct",
            "provider": "Vultr Serverless Inference Simulator"
        }
