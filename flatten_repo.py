import os

# ==========================
# Configuration
# ==========================

ROOT_DIR = "."                     # Repo root
OUTPUT_FILE = "flattened_repo.txt"

# Folders to ignore
IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".idea",
    ".vscode",
    "node_modules",
    ".terraform",
    "dist",
    "build"
}

# File extensions to ignore (binary or large)
IGNORE_EXTENSIONS = {
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".mp4",
    ".avi",
    ".zip",
    ".tar",
    ".gz",
    ".onnx",
    ".pt",
    ".pb",
    ".exe",
    ".dll"
}

# ==========================
# Helper Functions
# ==========================

def should_ignore(path):
    for part in path.split(os.sep):
        if part in IGNORE_DIRS:
            return True
    _, ext = os.path.splitext(path)
    return ext.lower() in IGNORE_EXTENSIONS


def is_text_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            f.read(1024)
        return True
    except Exception:
        return False


# ==========================
# Main Flatten Logic
# ==========================

def flatten_repository():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("==== FLATTENED REPOSITORY OUTPUT ====\n\n")

        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                file_path = os.path.join(root, file)

                if should_ignore(file_path):
                    continue

                if not is_text_file(file_path):
                    continue

                relative_path = os.path.relpath(file_path, ROOT_DIR)

                out.write("\n" + "=" * 80 + "\n")
                out.write(f"FILE: {relative_path}\n")
                out.write("=" * 80 + "\n\n")

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            out.write(line)
                except Exception as e:
                    out.write(f"\n[ERROR READING FILE: {e}]\n")

    print(f"✔ Repository flattened successfully into '{OUTPUT_FILE}'")


# ==========================
# Entry Point
# ==========================

if __name__ == "__main__":
    flatten_repository()
