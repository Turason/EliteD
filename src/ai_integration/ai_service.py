"""
AI Service Interface - Handles communication with online AI services.
Supports multiple AI providers (OpenAI, Anthropic, etc.) with a unified interface.
"""

import json
import asyncio
from typing import Dict, List, Optional, Union, Any
from enum import Enum
from dataclasses import dataclass
import time


class AIProvider(Enum):
    """Supported AI service providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"  # For local models like Ollama


@dataclass
class AIResponse:
    """Response from AI service."""
    content: str
    provider: AIProvider
    model: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None
    cost_estimate: Optional[float] = None
    error: Optional[str] = None


@dataclass
class AIConfig:
    """Configuration for AI service."""
    provider: AIProvider
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    max_tokens: int = 500
    temperature: float = 0.8
    timeout: int = 30


class AIService:
    """Main AI service interface."""
    
    def __init__(self, config: AIConfig):
        """Initialize AI service with configuration."""
        self.config = config
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider."""
        try:
            if self.config.provider == AIProvider.OPENAI:
                import openai
                self._client = openai.OpenAI(api_key=self.config.api_key)
            
            elif self.config.provider == AIProvider.ANTHROPIC:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.config.api_key)
            
            elif self.config.provider == AIProvider.AZURE_OPENAI:
                import openai
                self._client = openai.AzureOpenAI(
                    api_key=self.config.api_key,
                    azure_endpoint=self.config.api_base,
                    api_version="2024-02-15-preview"
                )
            
            elif self.config.provider == AIProvider.LOCAL:
                # For local models (Ollama, etc.)
                self._client = LocalAIClient(self.config.api_base or "http://localhost:11434")
            
        except ImportError as e:
            raise ImportError(f"Required package not installed for {self.config.provider.value}: {e}")
    
    async def generate_response(
        self, 
        system_prompt: str, 
        user_prompt: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> AIResponse:
        """Generate AI response from prompts."""
        
        start_time = time.time()
        
        try:
            # Build message history
            messages = []
            
            # Add system message
            if self.config.provider in [AIProvider.OPENAI, AIProvider.AZURE_OPENAI, AIProvider.LOCAL]:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    messages.append(msg)
            
            # Add current user message
            if self.config.provider == AIProvider.ANTHROPIC:
                # Anthropic handles system prompt separately
                user_content = f"System: {system_prompt}\n\nUser: {user_prompt}"
                messages.append({"role": "user", "content": user_content})
            else:
                messages.append({"role": "user", "content": user_prompt})
            
            # Generate response based on provider
            response = await self._call_ai_service(messages)
            
            response_time = time.time() - start_time
            response.response_time = response_time
            
            return response
            
        except Exception as e:
            return AIResponse(
                content="",
                provider=self.config.provider,
                model=self.config.model,
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _call_ai_service(self, messages: List[Dict[str, str]]) -> AIResponse:
        """Call the appropriate AI service."""
        
        if self.config.provider == AIProvider.OPENAI:
            return await self._call_openai(messages)
        
        elif self.config.provider == AIProvider.ANTHROPIC:
            return await self._call_anthropic(messages)
        
        elif self.config.provider == AIProvider.AZURE_OPENAI:
            return await self._call_azure_openai(messages)
        
        elif self.config.provider == AIProvider.LOCAL:
            return await self._call_local(messages)
        
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    async def _call_openai(self, messages: List[Dict[str, str]]) -> AIResponse:
        """Call OpenAI API."""
        try:
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.timeout
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider=self.config.provider,
                model=self.config.model,
                tokens_used=response.usage.total_tokens if response.usage else None,
                cost_estimate=self._estimate_cost_openai(response.usage) if response.usage else None
            )
        
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    async def _call_anthropic(self, messages: List[Dict[str, str]]) -> AIResponse:
        """Call Anthropic API."""
        try:
            # Extract the combined message content
            user_content = messages[-1]["content"]
            
            response = await asyncio.to_thread(
                self._client.messages.create,
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": user_content}]
            )
            
            return AIResponse(
                content=response.content[0].text,
                provider=self.config.provider,
                model=self.config.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                cost_estimate=self._estimate_cost_anthropic(response.usage)
            )
        
        except Exception as e:
            raise Exception(f"Anthropic API error: {e}")
    
    async def _call_azure_openai(self, messages: List[Dict[str, str]]) -> AIResponse:
        """Call Azure OpenAI API."""
        # Similar to OpenAI but with Azure client
        try:
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=self.config.model,  # This should be the deployment name
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.timeout
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider=self.config.provider,
                model=self.config.model,
                tokens_used=response.usage.total_tokens if response.usage else None
            )
        
        except Exception as e:
            raise Exception(f"Azure OpenAI API error: {e}")
    
    async def _call_local(self, messages: List[Dict[str, str]]) -> AIResponse:
        """Call local AI service (like Ollama)."""
        try:
            response = await self._client.generate(
                model=self.config.model,
                messages=messages,
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            )
            
            return AIResponse(
                content=response["message"]["content"],
                provider=self.config.provider,
                model=self.config.model,
                tokens_used=response.get("eval_count", 0) + response.get("prompt_eval_count", 0)
            )
        
        except Exception as e:
            raise Exception(f"Local AI error: {e}")
    
    def _estimate_cost_openai(self, usage) -> float:
        """Estimate cost for OpenAI API call."""
        # Rough cost estimation (prices change frequently)
        if "gpt-4" in self.config.model.lower():
            input_cost = usage.prompt_tokens * 0.00003  # $0.03 per 1K tokens
            output_cost = usage.completion_tokens * 0.00006  # $0.06 per 1K tokens
        elif "gpt-3.5" in self.config.model.lower():
            input_cost = usage.prompt_tokens * 0.0000015  # $0.0015 per 1K tokens
            output_cost = usage.completion_tokens * 0.000002  # $0.002 per 1K tokens
        else:
            return 0.0
        
        return input_cost + output_cost
    
    def _estimate_cost_anthropic(self, usage) -> float:
        """Estimate cost for Anthropic API call."""
        # Rough cost estimation for Claude
        if "claude-3-opus" in self.config.model.lower():
            input_cost = usage.input_tokens * 0.000015  # $15 per 1M tokens
            output_cost = usage.output_tokens * 0.000075  # $75 per 1M tokens
        elif "claude-3-sonnet" in self.config.model.lower():
            input_cost = usage.input_tokens * 0.000003  # $3 per 1M tokens
            output_cost = usage.output_tokens * 0.000015  # $15 per 1M tokens
        else:
            return 0.0
        
        return input_cost + output_cost


class LocalAIClient:
    """Simple client for local AI services like Ollama."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    async def generate(self, model: str, messages: List[Dict], options: Dict = None) -> Dict:
        """Generate response from local AI service."""
        import aiohttp
        
        # Convert messages to simple prompt for most local models
        prompt = self._messages_to_prompt(messages)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options or {}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "message": {"content": result.get("response", "")},
                        "eval_count": result.get("eval_count", 0),
                        "prompt_eval_count": result.get("prompt_eval_count", 0)
                    }
                else:
                    raise Exception(f"Local AI service returned status {response.status}")
    
    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert message format to simple prompt."""
        prompt_parts = []
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)


# Utility functions for easy setup
def create_openai_config(api_key: str, model: str = "gpt-4-turbo-preview") -> AIConfig:
    """Create OpenAI configuration."""
    return AIConfig(
        provider=AIProvider.OPENAI,
        api_key=api_key,
        model=model,
        max_tokens=500,
        temperature=0.8
    )


def create_anthropic_config(api_key: str, model: str = "claude-3-sonnet-20240229") -> AIConfig:
    """Create Anthropic configuration."""
    return AIConfig(
        provider=AIProvider.ANTHROPIC,
        api_key=api_key,
        model=model,
        max_tokens=500,
        temperature=0.8
    )


def create_local_config(model: str = "llama2", base_url: str = "http://localhost:11434") -> AIConfig:
    """Create local AI configuration (for Ollama, etc.)."""
    return AIConfig(
        provider=AIProvider.LOCAL,
        api_base=base_url,
        model=model,
        max_tokens=500,
        temperature=0.8
    )