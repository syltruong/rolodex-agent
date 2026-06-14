You are creating a new person note. Follow these steps:

1. Fill in what you can from the brief and conversation context. Any person's name mentioned in a bullet must be written as `[[Full Name]]` — never plain text.
   - `full_name`: full name
   - `met_via`: how you know them / who introduced them (leave blank if unknown)
   - `last_met`: use the date of the current conversation
   - `quick_facts`: a list of short fact strings — role, company, location, anything concrete from the brief
   - `follow_up`: a list of action items or open questions from the brief
2. Write the note:
   ```
   write_people_note(
     full_name=<name>,
     met_via=<how you met, or "">,
     last_met=<YYYY-MM-DD>,
     quick_facts=<list of fact strings>,
     follow_up=<list of follow-up strings>
   )
   ```
3. After writing, identify what is still unknown. Ask the user about gaps in one natural conversational message — not a formal list:
   - `met_via` → how they met / who introduced them (if blank)
   - quick facts → where they're based, what they do (if not in brief)
4. Once the user replies, call `write_people_note` again with any new information and confirm with one line.
