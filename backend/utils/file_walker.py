from pathlib import Path

EXCLUDED_DIRS = {'node_modules', 'dist', 'build', 'coverage', '.git', '.next', 'out'}
VALID_EXTENSIONS = ('.js', '.jsx', '.ts', '.tsx')

def walk_dir(root_path: str) -> list[str]:
    path = Path(root_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {root_path}")

    if path.is_file():
        return [str(path)] if path.suffix.lower() in VALID_EXTENSIONS else []

    file_list = []
    for file_path in path.rglob('*'):
        if not file_path.is_file() or file_path.suffix.lower() not in VALID_EXTENSIONS:
            continue
        if any(part in EXCLUDED_DIRS or part.startswith('.') for part in file_path.relative_to(path).parts[:-1]):
            continue
        file_list.append(str(file_path))
    return file_list