from pathlib import Path
import re
from agents import function_tool
import config

_PEOPLE_DIR = "People"
_CONVERSATIONS_DIR = "Conversations"

_TEMPLATE_MAP = {
    _PEOPLE_DIR: "_templates/Person.md",
    _CONVERSATIONS_DIR: "_templates/Conversation.md",
}

_FRONTMATTER_BLOCK_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)
_KV_RE = re.compile(r"^([\w_]+):\s*(.*)", re.MULTILINE)
_BLANK_VALUES = {"", "null", "~", "[]", "{}"}
_PLACEHOLDER_LINE_RE = re.compile(r"^\[.*\]$")

_BULLET_SECTIONS: dict[str, set[str]] = {
    _PEOPLE_DIR: {"Quick facts", "Recurring themes", "Conversations", "Follow-up"},
    _CONVERSATIONS_DIR: {"What we talked about", "What I want to remember", "Follow-up"},
}


def _vault() -> Path:
    if not config.OBSIDIAN_VAULT_ROOT:
        raise RuntimeError(
            "OBSIDIAN_VAULT_ROOT is not set in .env — "
            "point it at the root of your Obsidian vault."
        )
    return Path(config.OBSIDIAN_VAULT_ROOT).expanduser()


def _trash(path: str) -> None:
    """Move a vault-relative path to .trash/, preserving directory structure."""
    src = _vault() / path
    dst = _vault() / ".trash" / path
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)


def _parse_frontmatter(content: str) -> dict[str, str]:
    m = _FRONTMATTER_BLOCK_RE.match(content)
    if not m:
        return {}
    return dict(_KV_RE.findall(m.group(1)))


def _parse_sections(content: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    body: list[str] = []
    for line in content.splitlines():
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            if current is not None:
                sections[current] = "\n".join(body).strip()
            current = m.group(1).strip()
            body = []
        elif current is not None:
            body.append(line)
    if current is not None:
        sections[current] = "\n".join(body).strip()
    return sections


def _has_bullet_content(body: str) -> bool:
    real_lines = [
        l for l in body.splitlines()
        if l.strip() and not _PLACEHOLDER_LINE_RE.match(l.strip())
    ]
    if not real_lines:
        return True  # empty or placeholder-only — nothing to enforce
    return any(l.strip().startswith("- ") for l in real_lines)


def _schema_from_template(top_dir: str) -> dict:
    """Read the vault template for top_dir and return expected frontmatter keys + sections."""
    template_path = _TEMPLATE_MAP.get(top_dir)
    if not template_path:
        return {"frontmatter": [], "sections": []}
    full_path = _vault() / template_path
    if not full_path.exists():
        return {"frontmatter": [], "sections": []}
    content = full_path.read_text(encoding="utf-8")
    keys = list(_parse_frontmatter(content).keys())
    sections = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
    return {"frontmatter": keys, "sections": sections}


def _validate(top_dir: str, content: str) -> list[str]:
    schema = _schema_from_template(top_dir)
    if not schema["frontmatter"] and not schema["sections"]:
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
    sections_content = _parse_sections(content)
    for section in _BULLET_SECTIONS.get(top_dir, set()):
        if not _has_bullet_content(sections_content.get(section, "")):
            warnings.append(f"section '{section}' must use bullet points (- ), found prose")
    return warnings


def _write(path: str, content: str, top_dir: str) -> str:
    full_path = _vault() / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    warnings = _validate(top_dir, content)
    if not warnings:
        return f"Written: {path}"
    issues = "\n".join(f"  - {w}" for w in warnings)
    template = _TEMPLATE_MAP.get(top_dir, "unknown template")
    return (
        f"Written: {path} — SCHEMA ERRORS, note is incomplete.\n"
        f"You MUST fix all of the following before replying to the user:\n{issues}\n"
        f"Required action: call read_obsidian_note(\"{template}\") to re-check the expected "
        f"structure, correct the note content, and call the write tool again.\n"
        f"FILE CLEANUP: if fixing requires changing any parameter that affects the filename "
        f"(person_name, date, or context for conversations; full_name for people), you MUST "
        f"call trash_obsidian_note(\"{path}\") BEFORE writing the corrected version — "
        f"otherwise the broken file will remain as a duplicate."
    )


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
def write_people_note(full_name: str, content: str, previous_name: str = "") -> str:
    """Create or overwrite a person note at People/<full_name>.md.
    If previous_name is set and differs from full_name, the old People/<previous_name>.md is
    deleted after writing (use this when correcting a name, e.g. 'Alex' → 'Alex Strong').
    Returns a confirmation and any formatting warnings."""
    path = f"{_PEOPLE_DIR}/{full_name}.md"
    result = _write(path, content, _PEOPLE_DIR)
    if previous_name and previous_name != full_name:
        old = f"{_PEOPLE_DIR}/{previous_name}.md"
        if (_vault() / old).exists():
            _trash(old)
            result += f"\nMoved People/{previous_name}.md to .trash/ — update any [[{previous_name}]] wikilinks in conversation notes to [[{full_name}]]."
    return result


@function_tool
def trash_obsidian_note(path: str) -> str:
    """Move a note to Obsidian's .trash/ folder (excluded from graph view, recoverable via
    Obsidian's 'Restore deleted file'). Path is relative to the vault root.
    Only notes in People/ or Conversations/ can be trashed."""
    parts = Path(path).parts
    if not parts or parts[0] not in {_PEOPLE_DIR, _CONVERSATIONS_DIR}:
        return f"[error: can only trash notes in People/ or Conversations/, got '{path}']"
    if not (_vault() / path).exists():
        return f"[note not found: {path}]"
    _trash(path)
    return f"Moved to .trash/: {path}"


@function_tool
def write_conversation_note(date: str, person_name: str, context: str, content: str) -> str:
    """Create or overwrite a conversation note at Conversations/YYYY-MM-DD <person_name> <context>.md.
    date must be YYYY-MM-DD. Returns a confirmation and any formatting warnings."""
    path = f"{_CONVERSATIONS_DIR}/{date} {person_name} {context}.md"
    return _write(path, content, _CONVERSATIONS_DIR)


