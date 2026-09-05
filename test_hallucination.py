import os
from qwen_agent_colab.core.qwen_provider import QwenProvider
from qwen_agent_colab.core.agent import AutonomousAgent
from qwen_agent_colab.tools.filesystem import read_file, write_file, list_directory
from qwen_agent_colab.tools.terminal import execute_command

provider = QwenProvider(mode="fallback_api")

schemas = [
    {
        "name": "list_directory",
        "description": "Lists contents of a directory",
        "parameters": {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"]
        }
    },
    {
        "name": "read_file",
        "description": "Reads a file content",
        "parameters": {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}},
            "required": ["path"]
        }
    }
]

funcs = {
    "list_directory": list_directory,
    "read_file": read_file,
}

agent = AutonomousAgent(provider, schemas, funcs)

task = """
Verifique o conteúdo do arquivo 'test-sandbox/fantasma.txt'.
Se o arquivo não existir, não tente adivinhar. Reporte exatamente o que o ambiente diz.
"""

agent.run(task, max_iterations=3)
