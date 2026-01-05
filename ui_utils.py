# ui_utils.py
from PySide6.QtGui import QTextDocument


def html_preview(html: str, max_len: int = 120) -> str:
    """Μετατρέπει HTML σε plain text και το κόβει σε max_len χαρακτήρες."""
    doc = QTextDocument()
    doc.setHtml(html or "")
    text = doc.toPlainText().strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text
