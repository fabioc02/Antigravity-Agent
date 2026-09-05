import os
from qwen_agent_colab.core.llm_provider import NativeLLMProvider
api_key = os.environ.get("GEMINI_API_KEY")
provider = NativeLLMProvider(api_key)
res = provider.generate_content([{"role": "user", "parts": [{"text": "Hello"}]}])
print(res)
