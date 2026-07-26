from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import base64
import hashlib
import os


class AIProvider(ABC):
    """Base class for all AI vision providers."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or self._get_env_key()
        self.model = model or self._default_model()

    @abstractmethod
    def _get_env_key(self) -> Optional[str]:
        pass

    @abstractmethod
    def _default_model(self) -> str:
        pass

    @abstractmethod
    def analyze_image(self, image_bytes: bytes, prompt: str, **kwargs) -> Dict[str, Any]:
        pass

    def encode_image(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    def image_hash(self, image_bytes: bytes) -> str:
        return hashlib.sha256(image_bytes).hexdigest()
