from pathlib import Path

# הגדרות
OUTPUT_FILE = "full_project_context.md"
TARGET_EXTENSIONS = {".py", ".md"}  # אפשר להוסיף סיומות כמו .env.example, .toml, .sql
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
    "dist",
    "build",
}


def should_ignore(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def generate_tree(root: Path, prefix: str = "") -> list[str]:
    lines = []
    items = sorted(
        [p for p in root.iterdir() if not should_ignore(p)],
        key=lambda p: (p.is_file(), p.name.lower()),
    )

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{item.name}")

        if item.is_dir():
            new_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(generate_tree(item, new_prefix))

    return lines


def bundle_project(root_dir: str = "."):
    root = Path(root_dir).resolve()
    markdown_lines = []

    # 1. יצירת עץ התיקיות
    markdown_lines.append(f"# Project Overview: `{root.name}`\n")
    markdown_lines.append("## Directory Tree\n```text")
    markdown_lines.extend(generate_tree(root))
    markdown_lines.append("```\n")

    # 2. מעבר על הקבצים ואיחוד התוכן
    markdown_lines.append("## Source Files\n")
    py_files = sorted(
        [
            p
            for p in root.rglob("*")
            if p.is_file()
            and p.suffix in TARGET_EXTENSIONS
            and not should_ignore(p)
        ]
    )

    for file_path in py_files:
        relative_path = file_path.relative_to(root)
        markdown_lines.append(f"### `{relative_path}`\n")
        markdown_lines.append("```python")

        try:
            content = file_path.read_text(encoding="utf-8")
            markdown_lines.append(content)
        except Exception as e:
            markdown_lines.append(f"# Error reading file: {e}")

        markdown_lines.append("```\n")

    # שמירה לקובץ
    out_path = root / OUTPUT_FILE
    out_path.write_text("\n".join(markdown_lines), encoding="utf-8")
    print(
        f"Bundled {len(py_files)} files into '{OUTPUT_FILE}' successfully."
    )


if __name__ == "__main__":
    bundle_project()