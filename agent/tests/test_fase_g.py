import os
import shutil
import subprocess
from agent.github.manager import GitHubManager, PushBlockedError
from agent.git.manager import GitManager

def test_fase_g():
    print("[TESTE FASE G] Iniciando integracao GitHub (Simulada via bare repo)")
    ws_root = "/tmp/workspace_fase_g"
    remote_repo = "/tmp/remote_fase_g.git"
    
    if os.path.exists(ws_root): shutil.rmtree(ws_root)
    if os.path.exists(remote_repo): shutil.rmtree(remote_repo)
    
    os.makedirs(ws_root, exist_ok=True)
    os.makedirs(remote_repo, exist_ok=True)
    
    # 1. Setup Remote Bare Repo
    subprocess.run(["git", "init", "--bare"], cwd=remote_repo, capture_output=True)
    
    # 2. Setup Local Repo
    git = GitManager(ws_root)
    git.init()
    
    with open(os.path.join(ws_root, "main.py"), "w") as f:
        f.write("print('Hello World')")
    git.commit("Initial commit")
    
    gh = GitHubManager(ws_root)
    
    # 3. Test Config Missing
    print("\n--- Test Config Missing ---")
    conf = gh.check_config()
    assert conf["has_remote"] == False
    print("[OK] Absent config detected.")
    
    # 4. Test Set Remote
    print("\n--- Test Set Remote ---")
    gh.set_remote(remote_repo)
    conf = gh.check_config()
    assert conf["has_remote"] == True
    assert conf["remote_url"] == remote_repo
    print("[OK] Remote successfully set and detected.")
    
    # 5. Test Ahead/Behind & Prepare Push
    print("\n--- Test Ahead/Behind & Prepare ---")
    prep = gh.prepare_push()
    assert prep["ahead"] >= 1
    assert prep["behind"] == 0
    assert prep["working_tree_clean"] == True
    assert prep["can_push"] == True
    assert len(prep["secrets_flagged"]) == 0
    print("[OK] Ahead/Behind calculation and push preparation passed.")
    
    # 6. Test Block Push without Authorization
    print("\n--- Test Unauthorized Push ---")
    try:
        gh.push(authorized=False)
        assert False, "Should have blocked!"
    except PushBlockedError as e:
        assert "Explicit user authorization required" in str(e)
        print("[OK] Push blocked due to missing explicit authorization.")
    
    # 7. Test Successful Push
    print("\n--- Test Authorized Push ---")
    res = gh.push(authorized=True)
    assert res["success"] == True
    print("[OK] Authorized push succeeded.")
    
    # 8. Test Secret Detection
    print("\n--- Test Secret Detection ---")
    with open(os.path.join(ws_root, ".env"), "w") as f:
        f.write("API_KEY=123")
    git.commit("Add secret")
    
    prep_sec = gh.prepare_push()
    assert prep_sec["can_push"] == False
    assert ".env" in prep_sec["secrets_flagged"]
    
    try:
        gh.push(authorized=True)
        assert False, "Should have blocked secret!"
    except PushBlockedError as e:
        assert "Sensitive files detected" in str(e)
        print("[OK] Push blocked due to .env secret detection.")
        
    # Undo secret commit to test recovery
    subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=ws_root, capture_output=True)
    
    # 9. Test Push Recovery Mechanism
    print("\n--- Test Recovery Mechanism ---")
    # Our local HEAD is now equal to remote HEAD because we reset the secret commit.
    # Therefore, check_pushed() should return True.
    assert gh.check_pushed() == True
    print("[OK] Interrupted push recovery successfully identified local and remote HEAD match.")
    
    # 10. Test LLM Terminal Bypass Prevention

    from agent.security.sandbox import SecuritySandbox

    sandbox = SecuritySandbox(ws_root)

    try:

        sandbox.validate_command("git push origin main")

        assert False, "Should block git push"

    except PermissionError as e:

        assert "PUSH BLOCKED" in str(e)

    try:

        sandbox.validate_command("agent github push --authorized")

        assert False, "Should block agent push"

    except PermissionError as e:

        assert "PUSH BLOCKED" in str(e)

    print("[OK] LLM bypass of push authorization successfully blocked in Sandbox.")

    print("\nFASE G = APPROVED")

if __name__ == "__main__":
    test_fase_g()

