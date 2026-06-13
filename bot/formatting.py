import re
import html as _html


def md_to_html(text: str) -> str:
    """Convert a markdown-ish LLM response to Telegram-safe HTML.

    Telegram supports: <b>, <i>, <u>, <s>, <code>, <pre>, <a href>.
    Everything else must have &, <, > escaped.
    """
    # --- 1. Lift out fenced code blocks before any escaping ---
    blocks: list[str] = []

    def _save_block(m: re.Match) -> str:
        lang = (m.group(1) or "").strip()
        code = _html.escape(m.group(2))
        tag = f'<pre><code class="language-{lang}">{code}</code></pre>' if lang else f"<pre>{code}</pre>"
        blocks.append(tag)
        return f"\x00B{len(blocks)-1}\x00"

    text = re.sub(r"```(\w*)[ \t]*\n?(.*?)```", _save_block, text, flags=re.DOTALL)

    # --- 2. Lift out inline code ---
    inlines: list[str] = []

    def _save_inline(m: re.Match) -> str:
        inlines.append(f"<code>{_html.escape(m.group(1))}</code>")
        return f"\x00I{len(inlines)-1}\x00"

    text = re.sub(r"`([^`\n]+)`", _save_inline, text)

    # --- 3. Escape remaining HTML entities ---
    text = _html.escape(text)

    # --- 4. Markdown → HTML (order matters: bold before italic) ---
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__",     r"<b>\1</b>", text, flags=re.DOTALL)
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text, flags=re.DOTALL)
    text = re.sub(r"_(.+?)_",       r"<i>\1</i>", text, flags=re.DOTALL)
    text = re.sub(r"~~(.+?)~~",     r"<s>\1</s>", text, flags=re.DOTALL)
    # Strip heading markers, keep text (Telegram has no heading element)
    text = re.sub(r"^#{1,6} (.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # --- 5. Restore lifted blocks ---
    for i, tag in enumerate(blocks):
        text = text.replace(f"\x00B{i}\x00", tag)
    for i, tag in enumerate(inlines):
        text = text.replace(f"\x00I{i}\x00", tag)

    return text
