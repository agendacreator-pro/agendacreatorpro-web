import os
import io
import json
import base64
from typing import Optional, Dict, Any
from .base import AIProvider


class OpenAIProvider(AIProvider):

    def _get_env_key(self) -> Optional[str]:
        return os.environ.get("OPENAI_API_KEY")

    def _default_model(self) -> str:
        return "gpt-4o"

    def _resize_image(self, image_bytes: bytes, max_side: int = 1568) -> bytes:
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size
            if max(w, h) <= max_side:
                return image_bytes
            scale = max_side / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue()
        except Exception:
            return image_bytes

    def analyze_image(self, image_bytes: bytes, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")

        client = OpenAI(api_key=self.api_key)
        image_bytes = self._resize_image(image_bytes)
        b64 = self.encode_image(image_bytes)
        content_type = kwargs.get("content_type", "image/png")

        max_retries = 3
        last_err = None
        for attempt in range(max_retries + 1):
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a layout architect. Always respond with valid JSON only, no markdown, no code fences.",
                    },
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
                max_tokens=16384,
            )

            text = response.choices[0].message.content
            finish = response.choices[0].finish_reason
            print(f"[OPENAI ATTEMPT {attempt+1}] finish_reason={finish}, content_len={len(text) if text else 0}, content_preview={repr(text[:200]) if text else 'None'}")
            if text:
                text = text.strip()
                if text.startswith("```"):
                    lines = text.split("\n")
                    lines = [l for l in lines if not l.strip().startswith("```")]
                    text = "\n".join(lines)
                try:
                    return json.loads(text)
                except json.JSONDecodeError as je:
                    last_err = f"JSON parse error: {je}, content_start={repr(text[:100])}"
                    print(f"[OPENAI] {last_err}")
            else:
                last_err = f"empty content, finish_reason={finish}"

            finish = response.choices[0].finish_reason
            last_err = f"finish_reason={finish}"
            if attempt < max_retries:
                import time
                time.sleep(2)

        raise RuntimeError(
            f"OpenAI returned empty content after {max_retries+1} attempts ({last_err}). "
            f"Try a simpler image or different provider."
        )
