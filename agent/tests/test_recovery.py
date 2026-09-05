import os
import sys
import time

# Ensure agent is in path
DRIVE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, DRIVE_ROOT)

from agent.core.runtime import RuntimeManager

def test_recovery():
    print("=== TESTING SESSION RECOVERY ===")
    
    # 1. Initialize Runtime A
    rm_a = RuntimeManager(DRIVE_ROOT)
    assert rm_a.acquire_lock()
    rm_a.register_runtime()
    
    # 2. Start a session
    task = "Test task that will be interrupted"
    session_id = rm_a.start_session(task_id=task)
    print(f"Started session {session_id} on Runtime A ({rm_a.runtime_id})")
    
    # 3. Simulate some work
    rm_a.current_session['iteration'] = 3
    rm_a.current_session['last_action'] = {"tool": "filesystem.list", "args": {"path": "."}}
    rm_a.save_session()
    
    # 4. Simulate Runtime A crashing (losing lock but state is saved)
    print("Simulating Runtime A crash...")
    rm_a.release_lock()
    
    # Wait a bit
    time.sleep(1)
    
    # 5. Initialize Runtime B
    rm_b = RuntimeManager(DRIVE_ROOT)
    assert rm_b.acquire_lock()
    rm_b.register_runtime()
    print(f"Started Runtime B ({rm_b.runtime_id})")
    
    # 6. Attempt recovery
    last_session = rm_b.get_last_active_session()
    assert last_session == session_id
    print(f"Runtime B detected interrupted session {last_session}")
    
    session_data = rm_b.load_session(last_session)
    assert session_data is not None
    assert session_data['iteration'] == 3
    assert session_data['last_action']['tool'] == "filesystem.list"
    
    print("PASS: Session data fully recovered by Runtime B.")
    rm_b.release_lock()

if __name__ == "__main__":
    test_recovery()
