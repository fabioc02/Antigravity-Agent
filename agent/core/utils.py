import os
import tempfile
import json

def atomic_write_json(data: dict, filepath: str):
    dir_name = os.path.dirname(filepath)
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name)
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, indent=4)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, filepath)
