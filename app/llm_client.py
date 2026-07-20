from . import config
from openai import AzureOpenAI


def _client() -> AzureOpenAI:
    if not (config.AZURE_ENDPOINT and config.AZURE_API_KEY):
        raise RuntimeError(
            "Azure OpenAI credentials are missing. Copy .env.example to .env "
            "and fill in your values."
        )
    return AzureOpenAI(
        azure_endpoint=config.AZURE_ENDPOINT,
        api_key=config.AZURE_API_KEY,
        api_version=config.AZURE_API_VERSION,
    )