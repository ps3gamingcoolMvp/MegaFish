"""
LLM Client Wrapper
Unified OpenAI format API calls
Supports Ollama num_ctx parameter to prevent prompt truncation
Auto-fallback to local Ollama when primary API returns 403/401

Once any instance discovers the primary provider is down (403/401),
a module-level flag is set so ALL future instances skip the primary
immediately — no more wasted round-trips.
"""

import json
import os
import re
import threading
from typing import Optional, Dict, Any, List
from openai import OpenAI, AuthenticationError, PermissionDeniedError

from ..config import Config

import logging
_fallback_logger = logging.getLogger("megafish.llm_client")

# Module-level flag: set to True the first time any instance hits a 403/401.
# Thread-safe via _provider_lock.
_primary_provider_down = False
_provider_lock = threading.Lock()


def _mark_primary_down():
    global _primary_provider_down
    with _provider_lock:
        if not _primary_provider_down:
            _primary_provider_down = True
            _fallback_logger.warning(
                "Primary LLM provider marked as unavailable for this session. "
                "All future calls will go directly to local Ollama."
            )


class LLMClient:
    """
    LLM Client with automatic fallback.
    Primary: configured LLM_BASE_URL (e.g. Groq)
    Fallback: local Ollama on localhost:11434
    """

    OLLAMA_FALLBACK_URL   = "http://localhost:11434/v1"
    OLLAMA_FALLBACK_KEY   = "ollama"
    OLLAMA_FALLBACK_MODEL = "qwen2.5:1.5b"   # fast on CPU; 7b available for quality via env

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 1800.0
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY not configured")

        self._timeout = timeout
        self._num_ctx = int(os.environ.get('OLLAMA_NUM_CTX', '8192'))

        # If another instance already found the primary is down, start in fallback immediately
        with _provider_lock:
            primary_down = _primary_provider_down
        if primary_down:
            self._using_fallback = True
            self._init_ollama_client()
        else:
            self._using_fallback = False
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=timeout,
            )

    def _init_ollama_client(self):
        """Switch this instance to the Ollama client."""
        self.api_key  = self.OLLAMA_FALLBACK_KEY
        self.base_url = self.OLLAMA_FALLBACK_URL
        self.model    = os.environ.get("OLLAMA_FALLBACK_MODEL", self.OLLAMA_FALLBACK_MODEL)
        self.client   = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self._timeout,
        )

    def _is_ollama(self) -> bool:
        return '11434' in (self.base_url or '')

    def _build_kwargs(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict],
    ) -> dict:
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format
        if self._is_ollama() and self._num_ctx:
            kwargs["extra_body"] = {"options": {"num_ctx": self._num_ctx}}
        return kwargs

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        kwargs = self._build_kwargs(messages, temperature, max_tokens, response_format)

        # Already on fallback — call directly, no error handling overhead
        if self._using_fallback:
            return self._call_and_clean(kwargs)

        try:
            return self._call_and_clean(kwargs)

        except (AuthenticationError, PermissionDeniedError) as e:
            _fallback_logger.warning(f"Primary LLM auth error ({e}). Falling back to Ollama.")
            _mark_primary_down()
            self._activate_fallback(kwargs)
            return self._call_and_clean(kwargs)

        except Exception as e:
            if "403" in str(e) or "401" in str(e) or "access denied" in str(e).lower():
                _fallback_logger.warning(f"Primary LLM error (auth): {e}. Falling back to Ollama.")
                _mark_primary_down()
                self._activate_fallback(kwargs)
                return self._call_and_clean(kwargs)
            raise

    def _call_and_clean(self, kwargs: dict) -> str:
        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        # Strip <think>...</think> reasoning blocks (some models include these)
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content

    def _activate_fallback(self, kwargs: dict):
        """Switch this client instance to Ollama and update kwargs in-place."""
        if not self._using_fallback:
            self._using_fallback = True
            self._init_ollama_client()
            _fallback_logger.info(f"Fallback active: {self.base_url} / {self.model}")
        kwargs["model"] = self.model
        if self._num_ctx:
            kwargs["extra_body"] = {"options": {"num_ctx": self._num_ctx}}

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        # Ollama doesn't support json_object response format reliably
        fmt = {"type": "json_object"} if not self._is_ollama() else None
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=fmt,
        )
        cleaned = response.strip()
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from LLM: {cleaned}")
