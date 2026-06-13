from pathlib import Path
from agents import function_tool
import config


def _vault() -> Path:
    if not config.OBSIDIAN_VAULT_ROOT:
        raise RuntimeError(
            "OBSIDIAN_VAULT_ROOT is not set in .env — "
            "point it at the root of your Obsidian vault."
        )
    return Path(config.OBSIDIAN_VAULT_ROOT).expanduser()


@function_tool
def list_obsidian_notes(subdirectory: str = "") -> str:
    """List all Markdown notes in the Obsidian vault (or a subdirectory).
    Returns newline-separated paths relative to the vault root."""
    root = _vault()
    target = root / subdirectory if subdirectory else root
    notes = sorted(str(p.relative_to(root)) for p in target.rglob("*.md"))
    return "\n".join(notes) if notes else "(no notes found)"


@function_tool
def read_obsidian_note(path: str) -> str:
    """Read the full content of a note. Path is relative to the vault root."""
    full_path = _vault() / path
    if not full_path.exists():
        return f"[note not found: {path}]"
    return full_path.read_text(encoding="utf-8")


@function_tool
def write_obsidian_note(path: str, content: str) -> str:
    """Create or overwrite a Markdown note in the vault.
    Path is relative to the vault root. Parent directories are created as needed."""
    full_path = _vault() / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    return f"Written: {path}"
