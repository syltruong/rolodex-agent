You are checking for name collisions before writing any note. Follow these steps:

1. Call `list_people_notes` and scan the results for any file whose name starts with the same first name as the person mentioned in the brief.
2. If one or more matches are found:
   a. Read each matching note with `read_obsidian_note`.
   b. Ask the user to confirm before proceeding: "You mentioned [Name] — is this [Full Name] ([Works at / role])?"
   c. Do not write anything until you have an explicit confirmation.
3. If the person appears to be new but their first name matches an existing note:
   - Flag it clearly: "I already have a [Name] ([context]). Is this the same person or someone new?"
4. Never silently merge two different people into the same note.
5. Once the user confirms the identity (or confirms it's a new person), return to the calling skill and continue.
