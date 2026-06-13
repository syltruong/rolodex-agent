You are creating a new person note. Follow these steps:

1. Call `read_obsidian_note("_templates/Person.md")`. This is the exact skeleton — copy every frontmatter field and section heading verbatim.
2. Fill in every field you can from the brief and conversation context:
   - `name`: full name
   - `type`: always "person"
   - `tags`: infer from context (work, friend, investor, family, colleague, founder…). Do not ask the user.
   - `last_met`: use the date of the current conversation
   - `met_via`: fill if known, otherwise leave blank for follow-up
3. Write the note with `write_people_note(full_name, content)`.
4. After writing, identify every frontmatter field and section that is still blank. Ask the user about all of them in one conversational message — not a formal list, just natural questions:
   - `met_via` → how they met / who introduced them
   - `## Quick facts: Location` → where they're based
   - `## Quick facts: Works at` → role and company
   - `## About` → background, personality, anything worth remembering
   - `## Recurring themes` → topics that keep coming up with this person
5. Once the user replies, update the note with `write_people_note` and confirm with one line.
