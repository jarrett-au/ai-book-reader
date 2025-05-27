import os
from functools import lru_cache

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from termcolor import colored


@lru_cache(maxsize=1)
def get_llm(provider: str = "siliconflow", model: str = None):
    if provider == "siliconflow":
        print(colored(f"=== Using SiliconFlow LLM - {model} ===", "cyan"))
        return ChatOpenAI(
            model=model or os.getenv("SILICONFLOW_DEFAULT_MODEL"),
            base_url=os.getenv("SILICONFLOW_BASE_URL"),
            api_key=os.getenv("SILICONFLOW_API_KEY"),
        )
    elif provider == "azure":
        print(colored(f"=== Using Azure LLM - {model} ===", "cyan"))
        return AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_API_BASE"),
            azure_deployment=model or "gpt-4.1",
            api_version=os.getenv("AZURE_API_VERSION"),
            api_key=os.getenv("AZURE_API_KEY"),
        )
    elif provider == "302":
        print(colored(f"=== Using 302 LLM - {model} ===", "cyan"))
        return ChatOpenAI(
            model=model or "claude-3-7-sonnet-latest",
            base_url=os.getenv("302_BASE_URL"),
            api_key=os.getenv("302_API_KEY"),
        )
    else:
        raise ValueError(f"Invalid provider: {provider}")


chat_model = get_llm("azure")
