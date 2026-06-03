from pathlib import Path


def test_file_line_counts():
    """Assert that no code file in the codebase exceeds 150 lines."""
    root = Path(__file__).parent.parent
    extensions = {".py", ".html", ".css", ".js"}
    oversized_files = []

    for folder_name in ["alpha_kd", "tests"]:
        folder = root / folder_name
        if not folder.exists():
            continue
        for p in folder.rglob("*"):
            if p.is_file() and p.suffix in extensions:
                try:
                    lines = p.read_text(encoding="utf-8").splitlines()
                    count = len(lines)
                    if count > 150:
                        oversized_files.append((p.relative_to(root), count))
                except Exception:
                    pass

    assert not oversized_files, f"Oversized files (>150 lines): {oversized_files}"
