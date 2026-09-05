import os
import sys

# Ensure agent is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.security.sandbox import SecuritySandbox
from agent.tools.filesystem import WriteFileTool
from agent.tools.terminal import TerminalExecuteTool

def test_sandbox():
    print("Testing Security Sandbox...")
    sandbox = SecuritySandbox("/tmp/workspace")
    
    # Test valid path
    assert sandbox.validate_path("test.txt") == "/tmp/workspace/test.txt"
    
    # Test path traversal prevention
    try:
        sandbox.validate_path("../etc/passwd")
        print("FAIL: Path traversal allowed!")
        sys.exit(1)
    except PermissionError:
        print("PASS: Path traversal blocked.")
        
    # Test blocked command
    try:
        sandbox.validate_command("sudo rm -rf /")
        print("FAIL: Blocked command allowed!")
        sys.exit(1)
    except PermissionError:
        print("PASS: Blocked command caught.")

def test_tools():
    print("Testing Tools...")
    os.makedirs("/tmp/workspace", exist_ok=True)
    sandbox = SecuritySandbox("/tmp/workspace")
    
    writer = WriteFileTool(sandbox)
    res = writer.execute("hello.txt", "world")
    assert "Successfully wrote" in res
    print("PASS: WriteFileTool.")
    
    term = TerminalExecuteTool(sandbox)
    res = term.execute("cat hello.txt")
    assert "world" in res
    print("PASS: TerminalExecuteTool.")

if __name__ == "__main__":
    test_sandbox()
    test_tools()
    print("ALL TESTS PASSED.")
