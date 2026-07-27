import os
from enum import Enum
from typing import Dict, List, Optional

import requests

from src.config import settings
from src.utils.logger import log


class LLMProvider(str, Enum):
    """Available LLM providers"""

    OLLAMA = "ollama",
    GROQ = "groq",
    OPENAI = "openai",
    OPENROUTER = "openrouter"

class LLMClient:
    """provider agnostic llm client"""

    def __init__(self, provider: Optional[LLMProvider] = None):
        """"init the llm client"""

        self.provider = provider or self.get_default_provider()

        log.info(f"LLM client initialized with provider: {self.provider}")

        #init the appropriate provider
        if self.provider == LLMProvider.OLLAMA:
            self._init_ollama()
        elif self.provider == LLMProvider.OPENAI:
            self._init_openai()
        elif self.provider == LLMProvider.GROQ:
            self._init_groq()
        elif self.provider == LLMProvider.OPENROUTER:
            self._init_openrouter()
        else:
            raise ValueError(f"Unknown provider: {self.provider}")



    def get_default_provider(self) -> LLMProvider:
        """get the default provider from settings or environment"""
        # Check database first
        try:
            from app.db import get_llm_provider

            db_provider = get_llm_provider()
            if db_provider:
                provider_map = {
                    "groq": LLMProvider.GROQ,
                    "openrouter": LLMProvider.OPENROUTER,
                }
                if db_provider in provider_map:
                    return provider_map[db_provider]
        except Exception:
            pass  # Database not available

        if os.getenv("OPENROUTER_API_KEY"):
            return LLMProvider.OPENROUTER
        if(os.getenv("GROQ_API_KEY")):
            return LLMProvider.GROQ
        # if(os.getenv("GROQ_API_KEY")):
        #     return LLMProvider.OPENAI
        return LLMProvider.GROQ

    # OLLAMA INITIALIZATION
    def _init_ollama(self):
        """init the ollama client"""
        self.base_url = "http://localhost:11434"
        self.default_model = "qwen2:7b"

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout = 20)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                log.info(f"Ollama is running. Available models: {model_names}")

                if self.default_model not in model_names:
                    log.warning(f"Default model '{self.default_model}' not found.")
                    log.warning(f"Available: {model_names}")
                    log.warning(f"Pull it with: ollama pull {self.default_model}")
                else:
                    log.info(f"Default model '{self.default_model}' is available.")
        except requests.ConnectionError:
            log.error("Cannot connect to Ollama. Please ensure it's running.")
            log.error("Run: ollama serve")

    def _init_openrouter(self):
        """Initialize the OpenRouter client."""
        self.api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables.")

        # OpenRouter uses a simple HTTP API (no SDK needed)
        # We'll use requests directly
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = "google/gemma-4-31b-it:free"
        # self.default_model = "nvidia/nemotron-3-super-120b-a12b:free"

        log.info("OpenRouter client initialized successfully.")
        log.info(f"Default model: {self.default_model}")


    def _init_groq(self):
        try:
            from groq import Groq

            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in env vars")
            self.client = Groq(
                api_key=api_key,
                timeout=settings.llm.timeout if hasattr(settings, 'llm') else 60,
                max_retries=settings.llm.max_retries if hasattr(settings, 'llm') else 3,
            )
            self.default_model = "llama-3.3-70b-versatile"
            log.info("Groq client init successfully")
        except ImportError:
            log.error("Groq library not installed. Run: pip install openai")
            raise
        except Exception as e:
            log.error(f"Failed to initialize Groq: {e}")
            raise

    def _init_openai(self):
        try:
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in env vars")
            self.client = OpenAI(
                api_key=api_key,
                timeout=settings.llm.timeout if hasattr(settings, 'llm') else 60,
                max_retries=settings.llm.max_retries if hasattr(settings, 'llm') else 3,
            )
            self.default_model = "gpt_4o_mini"
            log.info("OpenAI client init successfully")
        except ImportError:
            log.error("OpenAI library not installed. Run: pip install openai")
            raise
        except Exception as e:
            log.error(f"Failed to initialize openAI: {e}")
            raise


    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """send a chat request to the LLM"""

        if self.provider == LLMProvider.OLLAMA:
            return self._chat_ollama(messages, model, temperature, max_tokens, **kwargs)
        elif self.provider == LLMProvider.OPENAI:
            return self._chat_openai(messages, model, temperature, max_tokens, **kwargs)
        elif self.provider == LLMProvider.GROQ:
            return self._chat_groq(messages, model, temperature, max_tokens, **kwargs)
        elif self.provider == LLMProvider.OPENROUTER:
            return self._chat_openrouter(messages, model, temperature, max_tokens, **kwargs)
        else:
            raise ValueError(f"Unknown Provider: {self.provider}")

    # OLLAMA CHAT IMPLEMENTATION
    def _chat_ollama(
            self,
            messages: List[Dict[str, str]],
            model: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            **kwargs
    ) -> str:
        """ chat with ollama local"""
        model = model or self.default_model
        temperature = temperature or 0.7
        max_tokens = max_tokens or 2048

        # convert messages to ollama format
        system_prompt = None
        user_prompt = None

        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content")
            elif msg.get("role") == "user":
                user_prompt = msg.get("content")

        # build prompt
        prompt = ""
        if system_prompt:
            prompt += f"System: {system_prompt}\n\n"
        if user_prompt:
            prompt += f"User: {user_prompt}\n\n"

        if not prompt and messages:
            prompt = messages[-1].get("content", "")
        log.debug(f"Ollama Request - Model: {model}")
        log.debug(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}")

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json = {
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,
                    **kwargs
                }, timeout=600
            )
            response.raise_for_status()
            result = response.json()
            content = result.get("response", "")

            log.debug(f"Ollama Response: {content[:100]}..." if len(content) > 100 else f"Ollama Response: {content}")
            return content

        except requests.exceptions.ConnectionError:
            log.error("Cannot connect to Ollama. Is it running? (ollama serve)")
            raise RuntimeError("Ollama is not running. Start it with: ollama serve")
        except requests.exceptions.Timeout:
            log.error("Ollama requests timed out")
        except requests.exceptions.RequestException as e:
            log.error(f"Ollama request failed: {e}")
            raise

    def _chat_openrouter(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Chat with OpenRouter (unified API, no rate limits)."""

        model = model or self.default_model
        temperature = temperature or 0.7
        max_tokens = max_tokens or 4096

        log.debug(f"OpenRouter Request - Model: {model}")
        log.debug(f"Messages: {len(messages)}")

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://competitorintel.local",  # Optional
                    "X-Title": "CompetitorIntel",  # Optional
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs,
                },
                timeout=60,
            )

            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            log.debug(
                f"OpenRouter Response: {content[:100]}..."
                if len(content) > 100
                else f"OpenRouter Response: {content}"
            )
            return content

        except requests.exceptions.Timeout:
            log.error("OpenRouter request timed out")
            raise
        except requests.exceptions.RequestException as e:
            log.error(f"OpenRouter request failed: {e}")
            raise
        except Exception as e:
            log.error(f"OpenRouter error: {e}")
            raise

    def _chat_groq(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Chat with Groq """

        model = model or self.default_model
        temperature = temperature or 0.7
        max_tokens = max_tokens or 4096

        log.debug(f"Groq Request - Model: {model}")
        log.debug(f"Messages: {len(messages)}")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            content = response.choices[0].message.content
            log.debug(
                f"Groq Response: {content[:100]}..."
                if len(content) > 100
                else f"Groq Response: {content}"
            )
            return content

        except Exception as e:
            log.error(f"Groq request failed: {e}")
            raise

    def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Chat with OpenAI (cloud, best quality, paid)."""

        model = model or self.default_model
        temperature = temperature or 0.7
        max_tokens = max_tokens or 4096

        log.debug(f"OpenAI Request - Model: {model}")
        log.debug(f"Messages: {len(messages)}")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            content = response.choices[0].message.content
            log.debug(
                f"OpenAI Response: {content[:100]}..."
                if len(content) > 100
                else f"OpenAI Response: {content}"
            )
            return content

        except Exception as e:
            log.error(f"OpenAI request failed: {e}")
            raise

    def chat_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Convenience method for chat with a system prompt."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return self.chat(
            messages=messages, model=model, temperature=temperature, max_tokens=max_tokens
        )

    def chat_with_history(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Chat with conversation history."""
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        return self.chat(
            messages=messages, model=model, temperature=temperature, max_tokens=max_tokens
        )

#SINGLETON INSTANCE
llm_client = LLMClient()

# TEST CODE

if __name__ == "__main__":
    """
    Test the LLM client.

    Run: python -m src.llm.client
    """

    print("=" * 60)
    print("CompetitorIntel - Provider-Agnostic LLM Client Test")
    print("=" * 60)

    print(f"\nUsing provider: {llm_client.provider}")

    # Check if default_model exists before accessing
    if hasattr(llm_client, "default_model") and llm_client.default_model:
        print(f"Default model: {llm_client.default_model}")
    else:
        print("Default model: Not set (check your provider configuration)")

    # Test 1: Basic chat
    print("\n--- Test 1: Basic Chat ---")
    try:
        response = llm_client.chat_with_system(
            system_prompt="You are a helpful assistant. Keep responses VERY short (1-2 words).",
            user_prompt="What is 2+2?",
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Longer response
    print("\n--- Test 2: Longer Response ---")
    try:
        response = llm_client.chat_with_system(
            system_prompt="You are a helpful assistant. Be concise.",
            user_prompt="Explain what an AI agent is in ONE sentence.",
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 3: Conversation history
    print("\n--- Test 3: Conversation History ---")
    try:
        messages = [
            {"role": "user", "content": "My name is Ahmad."},
            {"role": "assistant", "content": "Nice to meet you, Ahmad!"},
            {"role": "user", "content": "What's my name?"},
        ]

        response = llm_client.chat_with_history(
            messages=messages,
            system_prompt="You have a good memory. Always refer to people by name.",
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("LLM Client test complete!")
