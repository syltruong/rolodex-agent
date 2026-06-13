from pathlib import Path
import re
from agents import function_tool
import config

_PEOPLE_DIR = "People"
_CONVERSATIONS_DIR = "Conversations"

_SCHEMAS: dict[str, dict] = {
    _PEOPLE_DIR: {
        "frontmatter": ["tags", "met_via"],
        "sections": ["Quick facts", "About", "Recurring themes"],
    },
    _CONVERSATIONS_DIR: {
        "frontmatter": ["date", "people", "medium", "location"],
        "sections": ["Summary", "Topics", "Decisions", "Action items"],
    },
}

_FRONTMATTER_BLOCK_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)
_KV_RE = re.compile(r"^([\w_]+):\s*(.*)", re.MULTILINE)
_BLANK_VALUES = {"", "null", "~", "[]", "{}"}


def _vault() -> Path:
    if not config.OBSIDIAN_VAULT_ROOT:
        raise RuntimeError(
            "OBSIDIAN_VAULT_ROOT is not set in .env — "
            "point it at the root of your Obsidian vault."
        )
    return Path(config.OBSIDIAN_VAULT_ROOT).expanduser()


def _parse_frontmatter(content: str) -> dict[str, str]:
    m = _FRONTMATTER_BLOCK_RE.match(content)
    if not m:
        return {}
    return dict(_KV_RE.findall(m.group(1)))


def _validate(top_dir: str, content: str) -> list[str]:
    schema = _SCHEMAS.get(top_dir)
    if not schema:
        return []
    warnings: list[str] = []
    fm = _parse_frontmatter(content)
    if not fm and schema["frontmatter"]:
        warnings.append("no frontmatter block found")
    else:
        for key in schema["frontmatter"]:
            if key not in fm or fm[key].strip() in _BLANK_VALUES:
                warnings.append(f"missing frontmatter: {key}")
    present_sections = set(re.findall(r"^##\s+(.+)$", content, re.MULTILINE))
    for section in schema["sections"]:
        if section not in present_sections:
            warnings.append(f"missing section: {section}")
    return warnings


def _write(path: str, content: str, top_dir: str) -> str:
    full_path = _vault() / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    warnings = _validate(top_dir, content)
    result = f"Written: {path}"
    if warnings:
        result += "\n⚠ " + "\n⚠ ".join(warnings)
    return result


@function_tool
def list_people_notes() -> str:
    """List all Markdown notes in People/. Returns newline-separated paths relative to the vault root."""
    root = _vault()
    target = root / _PEOPLE_DIR
    if not target.exists():
        return "(no People/ directory found)"
    notes = sorted(str(p.relative_to(root)) for p in target.rglob("*.md"))
    return "\n".join(notes) if notes else "(no people notes found)"


@function_tool
def list_conversation_notes() -> str:
    """List all Markdown notes in Conversations/. Returns newline-separated paths relative to the vault root."""
    root = _vault()
    target = root / _CONVERSATIONS_DIR
    if not target.exists():
        return "(no Conversations/ directory found)"
    notes = sorted(str(p.relative_to(root)) for p in target.rglob("*.md"))
    return "\n".join(notes) if notes else "(no conversation notes found)"


@function_tool
def read_obsidian_note(path: str) -> str:
    """Read the full content of a note. Path is relative to the vault root."""
    full_path = _vault() / path
    if not full_path.exists():
        return f"[note not found: {path}]"
    return full_path.read_text(encoding="utf-8")


@function_tool
def write_people_note(full_name: str, content: str) -> str:
    """Create or overwrite a person note at People/<full_name>.md.
    Returns a confirmation and any formatting warnings."""
    path = f"{_PEOPLE_DIR}/{full_name}.md"
    return _write(path, content, _PEOPLE_DIR)


@function_tool
def write_conversation_note(date: str, person_name: str, context: str, content: str) -> str:
    """Create or overwrite a conversation note at Conversations/YYYY-MM-DD <person_name> <context>.md.
    date must be YYYY-MM-DD. Returns a confirmation and any formatting warnings."""
    path = f"{_CONVERSATIONS_DIR}/{date} {person_name} {context}.md"
    return _write(path, content, _CONVERSATIONS_DIR)
