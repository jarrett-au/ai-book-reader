import os

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from termcolor import colored


def get_llm(provider: str = None, model: str = None):
    # 如果没有传入provider，从环境变量读取
    if provider is None:
        provider = os.getenv("PROVIDER", "openai")
    
    if provider == "openai":
        print(colored(f"=== Using OpenAI Compatible LLM - {model} ===", "cyan"))
        return ChatOpenAI(
            model=model or os.getenv("OPENAI_DEFAULT_MODEL"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    elif provider == "azure":
        print(colored(f"=== Using Azure OpenAI LLM - {model} ===", "cyan"))
        return AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_API_BASE"),
            azure_deployment=model or "gpt-4.1",
            api_version=os.getenv("AZURE_API_VERSION"),
            api_key=os.getenv("AZURE_API_KEY"),
        )
    else:
        raise ValueError(f"Invalid provider: {provider}")


# 现在通过环境变量自动选择provider
chat_model = get_llm()
