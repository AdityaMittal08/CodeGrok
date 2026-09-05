import os

EXCLUDED_DIRS = {'node_modules', 'dist', 'build', 'coverage', '.git', '.next', 'out'}
VALID_EXTENSIONS = ('.js', '.jsx', '.ts', '.tsx')

def walk_dir(root_dir: str) -> list[str]:
    file_list = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith('.')]
        for f in filenames:
            if f.endswith(VALID_EXTENSIONS):
                file_list.append(os.path.join(dirpath, f))
    return file_list