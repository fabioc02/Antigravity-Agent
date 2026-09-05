import os
from qwen_agent_colab.core.qwen_provider import QwenProvider
from qwen_agent_colab.core.agent import AutonomousAgent
from qwen_agent_colab.tools.filesystem import read_file, write_file, list_directory
from qwen_agent_colab.tools.terminal import execute_command
from qwen_agent_colab.tools.memory import read_memory, update_memory
from qwen_agent_colab.tools.git import git_status, git_commit

# Forçando modo Fallback API no Sandbox porque não temos 16GB de VRAM
provider = QwenProvider(mode="fallback_api")

schemas = [
    {
        "name": "list_directory",
        "description": "Lists contents of a directory to see what files exist",
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
    },
    {
        "name": "write_file",
        "description": "Writes or overwrites content to a file",
        "parameters": {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}, "content": {"type": "STRING"}},
            "required": ["path", "content"]
        }
    },
    {
        "name": "execute_command",
        "description": "Executes a clean terminal command (e.g. 'python3 project/hello.py'). Do not use shell operators like &&",
        "parameters": {
            "type": "OBJECT",
            "properties": {"command": {"type": "STRING"}, "cwd": {"type": "STRING"}},
            "required": ["command"]
        }
    },
    {
        "name": "update_memory",
        "description": "Updates memory files like SESSION.md",
        "parameters": {
            "type": "OBJECT",
            "properties": {"file_name": {"type": "STRING"}, "content": {"type": "STRING"}, "cwd": {"type": "STRING"}},
            "required": ["file_name", "content"]
        }
    },
    {
        "name": "git_commit",
        "description": "Commits changes to git with a message",
        "parameters": {
            "type": "OBJECT",
            "properties": {"message": {"type": "STRING"}, "cwd": {"type": "STRING"}},
            "required": ["message"]
        }
    }
]

funcs = {
    "list_directory": list_directory,
    "read_file": read_file,
    "write_file": write_file,
    "execute_command": execute_command,
    "update_memory": update_memory,
    "git_commit": git_commit
}

agent = AutonomousAgent(provider, schemas, funcs)

task = """
Você é um agente de software autônomo.
Temos um repositório git em 'test-sandbox/project'.
Siga ESTES PASSOS estritamente:
1. Liste os arquivos em 'test-sandbox/project'.
2. Há um arquivo Python lá chamado hello.py (se não existir, não invente). Leia o arquivo.
3. Teste o arquivo executando 'python3 test-sandbox/project/hello.py'.
4. O arquivo contém um erro de compilação/sintaxe. Corrija o erro reescrevendo o arquivo corretamente via write_file. O erro deve ser resolvido mantendo a funcionalidade de dizer Hello World.
5. Execute 'python3 test-sandbox/project/hello.py' novamente para verificar se o exit code é 0. 
6. Se funcionar, crie um checkpoint git usando a ferramenta git_commit (use o cwd: 'test-sandbox/project') e atualize 'SESSION.md' usando update_memory.
"""

agent.run(task, max_iterations=8)
