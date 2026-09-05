import os
import shutil
import hashlib

class WorkspaceManager:
    def __init__(self, drive_root: str, project_id: str, local_workspace_root: str):
        self.project_id = project_id
        self.drive_project_source = os.path.join(drive_root, "projects", project_id, "source")
        self.local_dir = os.path.join(local_workspace_root, project_id)
        # IMPORTANTE: Removido '.git' da exclusao para garantir q history vá para o Drive!
        self.exclude_dirs = {'__pycache__', 'node_modules', '.gradle', 'build'}

    def _ignore_patterns(self, src, names):
        return [n for n in names if n in self.exclude_dirs]

    def sync_to_drive(self):
        os.makedirs(self.drive_project_source, exist_ok=True)
        if os.path.exists(self.local_dir):
            shutil.copytree(self.local_dir, self.drive_project_source, dirs_exist_ok=True, ignore=self._ignore_patterns)
        print(f"[WorkspaceManager] Synced local workspace to Drive: {self.drive_project_source}")

    def restore_from_drive(self):
        os.makedirs(self.local_dir, exist_ok=True)
        if os.path.exists(self.drive_project_source):
            shutil.copytree(self.drive_project_source, self.local_dir, dirs_exist_ok=True, ignore=self._ignore_patterns)
        print(f"[WorkspaceManager] Restored Drive project to local workspace: {self.local_dir}")

    def get_hash(self) -> str:
        if not os.path.exists(self.local_dir):
            return "empty"
        hasher = hashlib.sha256()
        for root, dirs, files in os.walk(self.local_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            for f in sorted(files):
                path = os.path.join(root, f)
                try:
                    with open(path, 'rb') as fp:
                        hasher.update(fp.read())
                except:
                    pass
        return hasher.hexdigest()
