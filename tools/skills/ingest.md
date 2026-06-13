You are processing a conversation brief. Follow these steps in order:

1. Extract from the brief: people (name, role), date, medium (call / in-person / Slack / etc.), location, topics, decisions, action items. Call `get_current_datetime` if no date was given.
2. For each person mentioned, run the ambiguity check: call load_skill("ambiguity") and follow it before touching any note.
3. For each person, call `list_people_notes` and then `read_obsidian_note` on their file if it exists.
4. Call `read_obsidian_note("_templates/Conversation.md")`. Use it as the exact skeleton — copy every frontmatter field and section heading verbatim. Do not invent structure from memory.
5. Write the conversation note with `write_conversation_note(date, person_name, context, content)`.
6. For each person:
   - Existing: update their note — add the new conversation wikilink to ## Conversations, sync any new follow-up items into ## Follow-up. Write with `write_people_note`.
   - New: call load_skill("new_person") and follow it.
7. If any write tool returns ⚠ warnings, fix the note and re-write it before replying.
8. Reply with one confirmation line listing files written and key facts captured.
