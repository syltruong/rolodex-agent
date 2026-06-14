from datetime import date as _date
from pathlib import Path
import re
from agents import function_tool
import config

_PEOPLE_DIR = "People"
_CONVERSATIONS_DIR = "Conversations"


_FRONTMATTER_BLOCK_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)
_KV_RE = re.compile(r"^([\w_]+):\s*(.*)", re.MULTILINE)


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


def _parse_sections(content: str) -> dict[str, list[str]]:
    """Return section title → list of bullet strings (without the leading '- ')."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in content.splitlines():
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
        elif current is not None and line.strip().startswith("- "):
            sections[current].append(line.strip()[2:])
    return sections


def _assemble_note(frontmatter: dict[str, str], sections: dict[str, list[str]]) -> str:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    for title, bullets in sections.items():
        lines.append("")
        lines.append(f"## {title}")
        lines.append("")
        for bullet in bullets:
            lines.append(f"- {bullet}")
    return "\n".join(lines) + "\n"


def _read_existing(path: str) -> str | None:
    full_path = _vault() / path
    return full_path.read_text(encoding="utf-8") if full_path.exists() else None


def _write(path: str, content: str) -> str:
    full_path = _vault() / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    return f"Written: {path}"


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
def write_people_note(
    full_name: str,
    met_via: str = "",
    last_met: str = "",
    quick_facts: list[str] | None = None,
    follow_up: list[str] | None = None,
    previous_name: str = "",
) -> str:
    """Create or update a person note at People/<full_name>.md.

    Frontmatter fields (name is always set from full_name):
      met_via   — how you know this person
      last_met  — date of last contact (YYYY-MM-DD)

    Sections (each is a list of bullet strings, without the leading '- '):
      quick_facts  — short facts about the person (appended to existing)
      follow_up    — things to do or ask next time (appended to existing)

    Omit a section arg to leave its existing bullets unchanged.
    Set previous_name when correcting a name so the old file is read and trashed."""
    path = f"{_PEOPLE_DIR}/{full_name}.md"
    source_path = f"{_PEOPLE_DIR}/{previous_name}.md" if previous_name else path
    existing = _read_existing(source_path)
    existing_fm = _parse_frontmatter(existing) if existing else {}
    existing_sections = _parse_sections(existing) if existing else {}

    fm = {
        "name": full_name,
        "met_via": met_via or existing_fm.get("met_via", ""),
        "last_met": last_met or existing_fm.get("last_met", ""),
    }
    sections = {
        "Quick facts": existing_sections.get("Quick facts", []) + (quick_facts if quick_facts is not None else []),
        "Follow-up": existing_sections.get("Follow-up", []) + (follow_up if follow_up is not None else []),
    }
    result = _write(path, _assemble_note(fm, sections))
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
def write_conversation_note(
    date: str,
    person_name: str,
    context: str,
    where: str = "",
    what_we_talked_about: list[str] | None = None,
    follow_up: list[str] | None = None,
) -> str:
    """Create or update a conversation note at Conversations/YYYY-MM-DD <person_name> <context>.md.

    Frontmatter fields (who/when are set from person_name/date):
      where  — location or medium (e.g. 'coffee', 'Zoom')

    Sections (each is a list of bullet strings, without the leading '- '):
      what_we_talked_about  — topics and key points from the conversation (appended to existing)
      follow_up             — actions or questions to carry forward (appended to existing)

    Omit a section arg to leave its existing bullets unchanged."""
    try:
        _date.fromisoformat(date)
    except ValueError:
        return f"[error: date must be YYYY-MM-DD, got '{date}']"
    path = f"{_CONVERSATIONS_DIR}/{date} {person_name} {context}.md"
    existing = _read_existing(path)
    existing_fm = _parse_frontmatter(existing) if existing else {}
    existing_sections = _parse_sections(existing) if existing else {}

    fm = {
        "who": person_name,
        "when": date,
        "where": where or existing_fm.get("where", ""),
    }
    sections = {
        "What we talked about": existing_sections.get("What we talked about", []) + (what_we_talked_about if what_we_talked_about is not None else []),
        "Follow-up": existing_sections.get("Follow-up", []) + (follow_up if follow_up is not None else []),
    }
    return _write(path, _assemble_note(fm, sections))
