from pathlib import Path
from agents import function_tool

_SKILLS_DIR = Path(__file__).parent / "skills"


@function_tool
def load_skill(name: str) -> str:
    """Load step-by-step instructions for a specific task.
    Available skills: ingest, new_person, ambiguity, retrieval."""
    path = _SKILLS_DIR / f"{name}.md"
    if not path.exists():
        available = sorted(p.stem for p in _SKILLS_DIR.glob("*.md"))
        return f"[skill '{name}' not found. Available: {', '.join(available)}]"
    return path.read_text(encoding="utf-8")
