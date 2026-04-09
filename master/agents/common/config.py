'''
Config class for the agents

Attributes:
    model: str
    api_key: str
    base_url: str
    model_id: str
    max_tokens: int
    temperature: float
'''
from pydantic_settings import BaseSettings
from typing import Optional

import os

class Settings(BaseSettings):
    def __init__(self):
        AGENT_SERVICE_PORT: int = 8000 # Port for the agent service
        GRADING_ENGINE_URL: str = "http://localhost:8001" # URL for the grading engine

        MONGODB_URI: str = "mongodb://localhost:27017/master_db" # URI for the MongoDB database

        # vLLM endpoints (H100 GPU server)
        VLLM_BASE_URL: str = "http://localhost" # Base URL for the vLLM server
        VLLM_MANAGER_PORT: int = 8080 # Port for the vLLM manager server
        VLLM_TEACHER_PORT: int = 8081 # Port for the vLLM teacher server
        VLLM_VERIFIER_PORT: int = 8082 # Port for the vLLM verifier server
        LLM_MANAGER_MODEL: str = "Qwen3-8B" # Model for the vLLM manager server
        LLM_TEACHER_MODEL: str = "Qwen3-14B-Quantized" # Model for the vLLM teacher server
        LLM_VERIFIER_MODEL: str = "Gemma-3-4B" # Model for the vLLM verifier server

        # Gemini fallback
        USE_GEMINI_FALLBACK: bool = False # Whether to use the Gemini fallback server
        GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") # API key for the Gemini fallback server
        GEMINI_MODEL: str = "gemini-2.5-flash" # Model for the Gemini fallback server

        # LLM defaults
        LLM_DEFAULT_TEMPERATURE: float = 0.3 # Default temperature for the LLM
        LLM_DEFAULT_TOP_P: float = 0.9 # Default top_p for the LLM
        LLM_DEFAULT_MAX_TOKENS: int = 4096 # Default maximum tokens for the LLM

        def get_vllm_url(self, agent_role: str) -> str:
            """
            Get the vLLM URL for the given agent role

            Args:
                agent_role: The role of the agent (manager, teacher, verifier)

            Returns:
                The vLLM URL for the given agent role
            """
            if agent_role not in ["manager", "teacher", "verifier"]:
                raise ValueError(f"Invalid agent role: {agent_role}")

            port_map = {
                "manager": self.VLLM_MANAGER_PORT,
                "teacher": self.VLLM_TEACHER_PORT,
                "verifier": self.VLLM_VERIFIER_PORT,
            }
            port = port_map.get(agent_role, self.VLLM_MANAGER_PORT)
            return f"{self.VLLM_BASE_URL}:{port}/v1"

        def get_model_name(self, agent_role: str) -> str:
            """
            Get the model name for the given agent role

            Args:
                agent_role: The role of the agent (manager, teacher, verifier)

            Returns:
                The model name for the given agent role
            """
            model_map = {
                "manager": self.LLM_MANAGER_MODEL,
                "teacher": self.LLM_TEACHER_MODEL,
                "verifier": self.LLM_VERIFIER_MODEL,
            }
            return model_map.get(agent_role, self.LLM_MANAGER_MODEL)

        model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()