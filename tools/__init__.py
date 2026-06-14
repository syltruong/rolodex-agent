from tools.datetime_tools import get_current_datetime
from tools.skill_tool import load_skill
from tools.obsidian_tools import (
    list_people_notes,
    list_conversation_notes,
    read_obsidian_note,
    trash_obsidian_note,
    write_people_note,
    write_conversation_note,
)

ALL_TOOLS = [
    load_skill,
    get_current_datetime,
    list_people_notes,
    list_conversation_notes,
    read_obsidian_note,
    trash_obsidian_note,
    write_people_note,
    write_conversation_note,
]
