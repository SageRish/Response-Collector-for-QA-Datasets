from enum import Enum
from dataclasses import dataclass

class Provider(Enum):
    OPENAI = "OpenAI"
    LM_STUDIO = "LM Studio"
    HUGGINGFACE = "Hugging Face"
    AZURE = "Azure"
    MISTRAL = "Mistral"
    GOOGLE = "Google"

@dataclass
class ModelConfig:
    alias: str
    provider: str  # Stored as string for easier UI handling
    model_name: str
    base_url: str
    api_key: str
