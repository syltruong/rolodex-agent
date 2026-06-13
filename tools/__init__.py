from tools.datetime_tools import get_current_datetime
from tools.obsidian_tools import list_obsidian_notes, read_obsidian_note, write_obsidian_note

ALL_TOOLS = [
    get_current_datetime,
    list_obsidian_notes,
    read_obsidian_note,
    write_obsidian_note,
]
