import os
import json
from typing import Optional, Dict, Any
from .base import AIProvider


class OpenAIProvider(AIProvider):

    def _get_env_key(self) -> Optional[str]:
        return os.environ.get("OPENAI_API_KEY")

    def _default_model(self) -> str:
        return "gpt-4o"

    def analyze_image(self, image_bytes: bytes, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")

        client = OpenAI(api_key=self.api_key)
        b64 = self.encode_image(image_bytes)
        content_type = kwargs.get("content_type", "image/png")

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_type};base64,{b64}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        text = response.choices[0].message.content
        return json.loads(text)
