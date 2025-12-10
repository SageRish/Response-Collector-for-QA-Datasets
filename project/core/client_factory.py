from openai import AsyncOpenAI
from .provider import ModelConfig

def make_client(model_cfg: ModelConfig) -> AsyncOpenAI:
    """
    Creates an AsyncOpenAI client based on the model configuration.
    All supported providers must be compatible with the OpenAI API.
    """
    return AsyncOpenAI(
        base_url=model_cfg.base_url,
        api_key=model_cfg.api_key
    )
