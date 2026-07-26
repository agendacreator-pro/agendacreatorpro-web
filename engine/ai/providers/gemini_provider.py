import os
import json
from typing import Optional, Dict, Any
from .base import AIProvider


class GeminiProvider(AIProvider):

    def _get_env_key(self) -> Optional[str]:
        return os.environ.get("GEMINI_API_KEY")

    def _default_model(self) -> str:
        return "gemini-2.0-flash"

    def analyze_image(self, image_bytes: bytes, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Install google-generativeai: pip install google-generativeai")

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)

        import PIL.Image
        from io import BytesIO
        img = PIL.Image.open(BytesIO(image_bytes))

        response = model.generate_content(
            [prompt, img],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            ),
        )

        return json.loads(response.text)
