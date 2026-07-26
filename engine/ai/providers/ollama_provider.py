import os
import json
import base64
import urllib.request
from typing import Optional, Dict, Any
from .base import AIProvider


class OllamaProvider(AIProvider):

    def _get_env_key(self) -> Optional[str]:
        return os.environ.get("OLLAMA_API_KEY")

    def _default_model(self) -> str:
        return "llava:latest"

    def analyze_image(self, image_bytes: bytes, prompt: str, **kwargs) -> Dict[str, Any]:
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        b64 = self.encode_image(image_bytes)

        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "images": [b64],
            "stream": False,
            "format": "json",
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        return json.loads(result.get("response", "{}"))
