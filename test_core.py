import json
from qwen_agent_colab.core.agent import AutonomousAgent
from qwen_agent_colab.tools.bridge_client import terminal_execute

class MockModel:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
        
    def generate(self, history):
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp
        return '{"action": "Finish"}'

if __name__ == "__main__":
    mock_responses = [
        '{"thought": "Preciso listar os arquivos", "action": "terminal_execute", "action_input": {"command": "ls"}}',
        '{"thought": "Vou criar um checkpoint Git", "action": "terminal_execute", "action_input": {"command": "git commit -m \\"test\\""}}',
        '{"thought": "Terminei", "action": "Finish"}'
    ]
    model = MockModel(mock_responses)
    agent = AutonomousAgent(model_provider=model, tools=[terminal_execute])
    agent.run("Faça um teste.")
