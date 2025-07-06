from fastapi import FastAPI, HTTPException, Depends, status, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any, AsyncGenerator
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import json
import httpx
import os
import time
import tiktoken
from enum import Enum
import structlog

from logging_config import setup_logging, get_llm_logger

# Logging konfigurieren
setup_logging("llm-proxy")
logger = get_llm_logger()

app = FastAPI(
    title="LLM Proxy Service",
    version="0.7.0",
    description="LLM Provider Abstraction Layer - Multi-Model Support"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ===================================================
# ENUMS & MODELS
# ===================================================

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    RUNPOD = "runpod"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str
    provider: LLMProvider
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=1, le=32000)
    stream: bool = False
    user_id: Optional[int] = None
    chat_id: Optional[int] = None

class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    provider: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, Any]
    cost: float
    request_id: str

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ModelConfig(BaseModel):
    name: str
    provider: LLMProvider
    input_cost_per_token: float
    output_cost_per_token: float
    max_tokens: int
    context_window: int
    supports_streaming: bool = True
    supports_functions: bool = False

# ===================================================
# MODEL CONFIGURATIONS
# ===================================================

MODEL_CONFIGS = {
    # OpenAI Models
    "gpt-4": ModelConfig(
        name="gpt-4",
        provider=LLMProvider.OPENAI,
        input_cost_per_token=0.00003,
        output_cost_per_token=0.00006,
        max_tokens=8192,
        context_window=8192,
        supports_streaming=True,
        supports_functions=True
    ),
    "gpt-4-turbo": ModelConfig(
        name="gpt-4-turbo",
        provider=LLMProvider.OPENAI,
        input_cost_per_token=0.00001,
        output_cost_per_token=0.00003,
        max_tokens=4096,
        context_window=128000,
        supports_streaming=True,
        supports_functions=True
    ),
    "gpt-3.5-turbo": ModelConfig(
        name="gpt-3.5-turbo",
        provider=LLMProvider.OPENAI,
        input_cost_per_token=0.0000015,
        output_cost_per_token=0.000002,
        max_tokens=4096,
        context_window=16384,
        supports_streaming=True,
        supports_functions=True
    ),
    
    # Anthropic Models
    "claude-3-sonnet-20240229": ModelConfig(
        name="claude-3-sonnet-20240229",
        provider=LLMProvider.ANTHROPIC,
        input_cost_per_token=0.000003,
        output_cost_per_token=0.000015,
        max_tokens=4096,
        context_window=200000,
        supports_streaming=True
    ),
    "claude-3-haiku-20240307": ModelConfig(
        name="claude-3-haiku-20240307",
        provider=LLMProvider.ANTHROPIC,
        input_cost_per_token=0.00000025,
        output_cost_per_token=0.00000125,
        max_tokens=4096,
        context_window=200000,
        supports_streaming=True
    ),
    
    # Google Models
    "gemini-pro": ModelConfig(
        name="gemini-pro",
        provider=LLMProvider.GOOGLE,
        input_cost_per_token=0.0000005,
        output_cost_per_token=0.0000015,
        max_tokens=8192,
        context_window=32768,
        supports_streaming=True
    ),
    
    # DeepSeek Models
    "deepseek-chat": ModelConfig(
        name="deepseek-chat",
        provider=LLMProvider.DEEPSEEK,
        input_cost_per_token=0.00000014,
        output_cost_per_token=0.00000028,
        max_tokens=4096,
        context_window=32768,
        supports_streaming=True
    ),
    
    # OpenRouter Models
    "openrouter/auto": ModelConfig(
        name="openrouter/auto",
        provider=LLMProvider.OPENROUTER,
        input_cost_per_token=0.000002,
        output_cost_per_token=0.000002,
        max_tokens=4096,
        context_window=8192,
        supports_streaming=True
    ),
    
    # RunPod Models
    "runpod/llama-2-70b": ModelConfig(
        name="runpod/llama-2-70b",
        provider=LLMProvider.RUNPOD,
        input_cost_per_token=0.0000008,
        output_cost_per_token=0.0000008,
        max_tokens=4096,
        context_window=4096,
        supports_streaming=True
    )
}

# ===================================================
# PROVIDER CLASSES
# ===================================================

class BaseProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def generate_completion(self, request: ChatRequest) -> ChatResponse:
        raise NotImplementedError
    
    async def generate_streaming_completion(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        raise NotImplementedError
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        config = MODEL_CONFIGS.get(model)
        if not config:
            return 0.0
        
        input_cost = input_tokens * config.input_cost_per_token
        output_cost = output_tokens * config.output_cost_per_token
        return input_cost + output_cost
    
    def count_tokens(self, text: str, model: str) -> int:
        try:
            encoding = tiktoken.encoding_for_model(model.split("/")[-1])
            return len(encoding.encode(text))
        except:
            # Fallback: rough estimate
            return len(text.split()) * 1.3

class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.openai.com/v1"
    
    async def generate_completion(self, request: ChatRequest) -> ChatResponse:
        logger.info("Generating OpenAI completion", model=request.model)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": request.model,
            "messages": [{"role": msg.role.value, "content": msg.content} for msg in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate cost
            usage = data.get("usage", {})
            cost = self.calculate_cost(
                request.model,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0)
            )
            
            processing_time = time.time() - start_time
            
            logger.info("OpenAI completion generated", 
                       model=request.model, 
                       tokens=usage.get("total_tokens", 0),
                       cost=cost,
                       processing_time=processing_time)
            
            return ChatResponse(
                id=data["id"],
                created=data["created"],
                model=request.model,
                provider=LLMProvider.OPENAI.value,
                choices=data["choices"],
                usage=usage,
                cost=cost,
                request_id=data.get("id", "")
            )
            
        except httpx.HTTPError as e:
            logger.error("OpenAI API error", error=str(e))
            raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")
    
    async def generate_streaming_completion(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        logger.info("Generating OpenAI streaming completion", model=request.model)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": request.model,
            "messages": [{"role": msg.role.value, "content": msg.content} for msg in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True
        }
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            yield f"data: {json.dumps(chunk)}\n\n"
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPError as e:
            logger.error("OpenAI streaming API error", error=str(e))
            raise HTTPException(status_code=502, detail=f"OpenAI streaming API error: {str(e)}")

class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.anthropic.com/v1"
    
    async def generate_completion(self, request: ChatRequest) -> ChatResponse:
        logger.info("Generating Anthropic completion", model=request.model)
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert messages to Anthropic format
        system_message = None
        messages = []
        
        for msg in request.messages:
            if msg.role == MessageRole.SYSTEM:
                system_message = msg.content
            else:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        payload = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": messages
        }
        
        if system_message:
            payload["system"] = system_message
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate tokens and cost
            input_tokens = self.count_tokens(
                " ".join([msg.content for msg in request.messages]),
                request.model
            )
            output_tokens = self.count_tokens(
                data["content"][0]["text"],
                request.model
            )
            
            cost = self.calculate_cost(request.model, input_tokens, output_tokens)
            
            processing_time = time.time() - start_time
            
            logger.info("Anthropic completion generated",
                       model=request.model,
                       input_tokens=input_tokens,
                       output_tokens=output_tokens,
                       cost=cost,
                       processing_time=processing_time)
            
            return ChatResponse(
                id=data["id"],
                created=int(time.time()),
                model=request.model,
                provider=LLMProvider.ANTHROPIC.value,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": data["content"][0]["text"]
                    },
                    "finish_reason": "stop"
                }],
                usage={
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                },
                cost=cost,
                request_id=data["id"]
            )
            
        except httpx.HTTPError as e:
            logger.error("Anthropic API error", error=str(e))
            raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

class GoogleProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def generate_completion(self, request: ChatRequest) -> ChatResponse:
        logger.info("Generating Google completion", model=request.model)
        
        # Convert messages to Google format
        contents = []
        for msg in request.messages:
            role = "user" if msg.role == MessageRole.USER else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
                "topP": 1.0,
                "topK": 1
            }
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{self.base_url}/models/{request.model}:generateContent?key={self.api_key}",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "candidates" not in data or not data["candidates"]:
                raise HTTPException(status_code=502, detail="No response from Google API")
            
            candidate = data["candidates"][0]
            content = candidate["content"]["parts"][0]["text"]
            
            # Calculate tokens and cost
            input_tokens = self.count_tokens(
                " ".join([msg.content for msg in request.messages]),
                request.model
            )
            output_tokens = self.count_tokens(content, request.model)
            
            cost = self.calculate_cost(request.model, input_tokens, output_tokens)
            
            processing_time = time.time() - start_time
            
            logger.info("Google completion generated",
                       model=request.model,
                       input_tokens=input_tokens,
                       output_tokens=output_tokens,
                       cost=cost,
                       processing_time=processing_time)
            
            return ChatResponse(
                id=f"google-{int(time.time())}",
                created=int(time.time()),
                model=request.model,
                provider=LLMProvider.GOOGLE.value,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }],
                usage={
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                },
                cost=cost,
                request_id=f"google-{int(time.time())}"
            )
            
        except httpx.HTTPError as e:
            logger.error("Google API error", error=str(e))
            raise HTTPException(status_code=502, detail=f"Google API error: {str(e)}")

class DeepSeekProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.deepseek.com/v1"
    
    async def generate_completion(self, request: ChatRequest) -> ChatResponse:
        logger.info("Generating DeepSeek completion", model=request.model)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": request.model,
            "messages": [{"role": msg.role.value, "content": msg.content} for msg in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate cost
            usage = data.get("usage", {})
            cost = self.calculate_cost(
                request.model,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0)
            )
            
            processing_time = time.time() - start_time
            
            logger.info("DeepSeek completion generated",
                       model=request.model,
                       tokens=usage.get("total_tokens", 0),
                       cost=cost,
                       processing_time=processing_time)
            
            return ChatResponse(
                id=data["id"],
                created=data["created"],
                model=request.model,
                provider=LLMProvider.DEEPSEEK.value,
                choices=data["choices"],
                usage=usage,
                cost=cost,
                request_id=data.get("id", "")
            )
            
        except httpx.HTTPError as e:
            logger.error("DeepSeek API error", error=str(e))
            raise HTTPException(status_code=502, detail=f"DeepSeek API error: {str(e)}")

class OpenRouterProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://openrouter.ai/api/v1"
    
    async def generate_completion(self, request: ChatRequest) -> ChatResponse:
        logger.info("Generating OpenRouter completion", model=request.model)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://llm-frontend.local",
            "X-Title": "LLM Frontend"
        }
        
        payload = {
            "model": request.model,
            "messages": [{"role": msg.role.value, "content": msg.content} for msg in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate cost
            usage = data.get("usage", {})
            cost = self.calculate_cost(
                request.model,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0)
            )
            
            processing_time = time.time() - start_time
            
            logger.info("OpenRouter completion generated",
                       model=request.model,
                       tokens=usage.get("total_tokens", 0),
                       cost=cost,
                       processing_time=processing_time)
            
            return ChatResponse(
                id=data["id"],
                created=data["created"],
                model=request.model,
                provider=LLMProvider.OPENROUTER.value,
                choices=data["choices"],
                usage=usage,
                cost=cost,
                request_id=data.get("id", "")
            )
            
        except httpx.HTTPError as e:
            logger.error("OpenRouter API error", error=str(e))
            raise HTTPException(status_code=502, detail=f"OpenRouter API error: {str(e)}")

class RunPodProvider(BaseProvider):
    def __init__(self, api_key: str, endpoint_url: str):
        super().__init__(api_key)
        self.base_url = endpoint_url
    
    async def generate_completion(self, request: ChatRequest) -> ChatResponse:
        logger.info("Generating RunPod completion", model=request.model)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": request.model,
            "messages": [{"role": msg.role.value, "content": msg.content} for msg in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate cost
            usage = data.get("usage", {})
            cost = self.calculate_cost(
                request.model,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0)
            )
            
            processing_time = time.time() - start_time
            
            logger.info("RunPod completion generated",
                       model=request.model,
                       tokens=usage.get("total_tokens", 0),
                       cost=cost,
                       processing_time=processing_time)
            
            return ChatResponse(
                id=data.get("id", f"runpod-{int(time.time())}"),
                created=data.get("created", int(time.time())),
                model=request.model,
                provider=LLMProvider.RUNPOD.value,
                choices=data["choices"],
                usage=usage,
                cost=cost,
                request_id=data.get("id", "")
            )
            
        except httpx.HTTPError as e:
            logger.error("RunPod API error", error=str(e))
            raise HTTPException(status_code=502, detail=f"RunPod API error: {str(e)}")

# ===================================================
# PROVIDER FACTORY
# ===================================================

def get_provider(provider: LLMProvider, api_key: str, endpoint_url: str = None) -> BaseProvider:
    """
    Factory function to get the appropriate provider
    """
    if provider == LLMProvider.OPENAI:
        return OpenAIProvider(api_key)
    elif provider == LLMProvider.ANTHROPIC:
        return AnthropicProvider(api_key)
    elif provider == LLMProvider.GOOGLE:
        return GoogleProvider(api_key)
    elif provider == LLMProvider.DEEPSEEK:
        return DeepSeekProvider(api_key)
    elif provider == LLMProvider.OPENROUTER:
        return OpenRouterProvider(api_key)
    elif provider == LLMProvider.RUNPOD:
        return RunPodProvider(api_key, endpoint_url or "https://api.runpod.ai")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

# ===================================================
# DEPENDENCY INJECTION
# ===================================================

async def get_api_key(request: Request, provider: LLMProvider) -> str:
    """
    Extract API key from request headers
    """
    header_name = f"X-{provider.value.upper()}-API-KEY"
    api_key = request.headers.get(header_name)
    
    if not api_key:
        # Fallback to environment variable
        env_var = f"{provider.value.upper()}_API_KEY"
        api_key = os.getenv(env_var)
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail=f"API key required for {provider.value}. Provide via {header_name} header or {env_var} environment variable"
        )
    
    return api_key

# ===================================================
# MAIN ENDPOINTS
# ===================================================

@app.on_event("startup")
async def startup_event():
    logger.info("LLM Proxy Service starting up")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("LLM Proxy Service shutting down")

@app.get("/")
def read_root():
    return {
        "message": "LLM Proxy Service v0.7.0",
        "providers": list(LLMProvider),
        "models": list(MODEL_CONFIGS.keys())
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "llm-proxy",
        "version": "0.7.0",
        "supported_providers": list(LLMProvider)
    }

@app.get("/models")
def list_models():
    """
    List all available models with their configurations
    """
    return {
        "models": [
            {
                "name": config.name,
                "provider": config.provider.value,
                "input_cost_per_token": config.input_cost_per_token,
                "output_cost_per_token": config.output_cost_per_token,
                "max_tokens": config.max_tokens,
                "context_window": config.context_window,
                "supports_streaming": config.supports_streaming,
                "supports_functions": config.supports_functions
            }
            for config in MODEL_CONFIGS.values()
        ]
    }

@app.post("/chat/completions")
async def chat_completions(
    request: ChatRequest,
    http_request: Request,
    background_tasks: BackgroundTasks
):
    """
    Generate chat completions using the specified provider
    """
    logger.info("Chat completion requested", 
               model=request.model, 
               provider=request.provider.value,
               stream=request.stream)
    
    # Get API key
    api_key = await get_api_key(http_request, request.provider)
    
    # Get provider instance
    provider = get_provider(request.provider, api_key)
    
    # Validate model
    if request.model not in MODEL_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Model {request.model} not supported"
        )
    
    try:
        if request.stream:
            # Return streaming response
            async def generate():
                async for chunk in provider.generate_streaming_completion(request):
                    yield chunk
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Return regular response
            response = await provider.generate_completion(request)
            
            # Log usage in background
            background_tasks.add_task(
                log_usage,
                request.user_id,
                request.chat_id,
                request.provider.value,
                request.model,
                response.usage,
                response.cost
            )
            
            return response
            
    except Exception as e:
        logger.error("Chat completion error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tokens/count")
async def count_tokens(
    text: str,
    model: str = "gpt-3.5-turbo"
):
    """
    Count tokens in text for a specific model
    """
    try:
        encoding = tiktoken.encoding_for_model(model.split("/")[-1])
        tokens = len(encoding.encode(text))
        
        return {
            "text": text,
            "model": model,
            "tokens": tokens,
            "characters": len(text)
        }
    except Exception as e:
        # Fallback counting
        tokens = int(len(text.split()) * 1.3)
        return {
            "text": text,
            "model": model,
            "tokens": tokens,
            "characters": len(text),
            "method": "fallback"
        }

@app.post("/cost/estimate")
async def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int
):
    """
    Estimate cost for a given model and token count
    """
    config = MODEL_CONFIGS.get(model)
    if not config:
        raise HTTPException(status_code=400, detail=f"Model {model} not found")
    
    input_cost = input_tokens * config.input_cost_per_token
    output_cost = output_tokens * config.output_cost_per_token
    total_cost = input_cost + output_cost
    
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
        "currency": "USD"
    }

# ===================================================
# BACKGROUND TASKS
# ===================================================

async def log_usage(
    user_id: Optional[int],
    chat_id: Optional[int],
    provider: str,
    model: str,
    usage: Dict[str, Any],
    cost: float
):
    """
    Log usage statistics (to be sent to backend-core)
    """
    logger.info("Usage logged",
               user_id=user_id,
               chat_id=chat_id,
               provider=provider,
               model=model,
               usage=usage,
               cost=cost)
    
    # TODO: Send to backend-core service for database logging
    # This would be implemented as an HTTP request to backend-core
    pass

# ===================================================
# ERROR HANDLING
# ===================================================

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "status_code": 500
    }