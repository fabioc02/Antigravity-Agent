from abc import ABC, abstractmethod

class Tool(ABC):
    name: str
    description: str
    permission_level: str
    
    def __init__(self, sandbox):
        self.sandbox = sandbox

    @abstractmethod
    def execute(self, **kwargs) -> str:
        pass
