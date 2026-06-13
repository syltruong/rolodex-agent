from pathlib import Path
from collections import defaultdict
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
_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2} .+")
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]+)?\]\]")
_SKIP_DIRS = {"_templates", ".obsidian"}
_SKIP_FILES = {"CLAUDE.md"}


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


@function_tool
def audit_vault() -> str:
    """Scan the vault for structural issues: wrong file locations, naming convention
    violations, broken [[wikilinks]], and missing frontmatter/sections.
    Returns a grouped report ready to share with the user."""
    root = _vault()
    all_notes = [
        p for p in root.rglob("*.md")
        if not any(part in _SKIP_DIRS for part in p.parts)
        and p.name not in _SKIP_FILES
    ]

    # Build stem index for wikilink resolution (Obsidian matches by filename stem)
    stem_index: dict[str, list[str]] = defaultdict(list)
    for note in all_notes:
        stem_index[note.stem.lower()].append(str(note.relative_to(root)))

    issues: dict[str, list[str]] = {
        "wrong location": [],
        "naming convention": [],
        "broken wikilinks": [],
        "formatting": [],
    }

    known_dirs = {_PEOPLE_DIR, _CONVERSATIONS_DIR}

    for note in sorted(all_notes):
        rel = str(note.relative_to(root))
        depth = len(note.relative_to(root).parts)
        top_dir = note.relative_to(root).parts[0] if depth > 1 else ""
        content = note.read_text(encoding="utf-8")

        # Location
        if depth == 1:
            issues["wrong location"].append(f"{rel} — stray note at vault root")
        elif top_dir not in known_dirs:
            issues["wrong location"].append(f"{rel} — unexpected directory '{top_dir}'")

        # Naming convention
        if top_dir == _CONVERSATIONS_DIR and not _DATE_PREFIX_RE.match(note.name):
            issues["naming convention"].append(
                f"{rel} — conversation filename must start with YYYY-MM-DD"
            )

        # Broken wikilinks
        for raw_link in _WIKILINK_RE.findall(content):
            target = raw_link.strip()
            if "/" in target:
                # Explicit path — check exact file
                if not (root / f"{target}.md").exists():
                    issues["broken wikilinks"].append(f"{rel} → [[{target}]]")
            else:
                if target.lower() not in stem_index:
                    issues["broken wikilinks"].append(f"{rel} → [[{target}]]")

        # Formatting (frontmatter + sections)
        for warning in _validate(top_dir, content):
            issues["formatting"].append(f"{rel} — {warning}")

    total = sum(len(v) for v in issues.values())
    if total == 0:
        return f"Audit passed — no issues found across {len(all_notes)} notes."

    lines: list[str] = []
    for category, items in issues.items():
        if items:
            lines.append(f"**{category}** ({len(items)})")
            lines.extend(f"  - {item}" for item in items)
            lines.append("")
    lines.append(f"Total: {total} issue(s) across {len(all_notes)} notes.")
    return "\n".join(lines)
