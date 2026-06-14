You are processing a conversation brief. Follow these steps in order:

1. Extract from the brief: person's name, date of conversation, context, what was discussed, what needs a follow-upπ. Call `get_current_datetime` to infer today's date and infer the date of the encounter, if not already mentioned explicitly.
2. For each person mentioned, run the ambiguity check: call load_skill("ambiguity") and follow it before touching any note.
3. For each person, call `list_people_notes` and then `read_obsidian_note` on their file if it exists — use this to avoid duplicating facts you already have.
4. Write the conversation note:
   ```
   write_conversation_note(
     date=<YYYY-MM-DD>,
     person_name=<name>,
     context=<context of conversation>,
     where=<medium or location>,
     what_we_talked_about=<list of topic strings>,
     follow_up=<list of action item strings>
   )
   ```
   Any person's name mentioned in a bullet must be written as `[[Full Name]]` — never plain text.
5. For each person:
   - Existing: update their note — append any new facts to `quick_facts` and new follow-up items to `follow_up`. Set `last_met` to today's date.
     ```
     write_people_note(
       full_name=<name>,
       last_met=<YYYY-MM-DD>,
       quick_facts=<list of newly learned facts, or omit if none>,
       follow_up=<list of new follow-up items, or omit if none>,
       previous_name=<file stem from ambiguity check, only if name changed>
     )
     ```
   - New: call load_skill("new_person") and follow it.
6. Reply with one confirmation line listing files written and key facts captured.
