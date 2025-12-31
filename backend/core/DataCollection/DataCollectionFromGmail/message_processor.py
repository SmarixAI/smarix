import base64
import quopri
from html import unescape


def _safe_decode_base64(data_b64: str) -> str:
    if not data_b64:
        return ""
    try:
        decoded_bytes = base64.urlsafe_b64decode(data_b64.encode("utf-8"))
        return decoded_bytes.decode("utf-8", errors="ignore")
    except Exception:
        try:
            return base64.b64decode(data_b64).decode("utf-8", errors="ignore")
        except Exception:
            return ""


def _decode_quoted_printable(text: str) -> str:
    try:
        return quopri.decodestring(text).decode("utf-8", errors="ignore")
    except Exception:
        return text or ""


def extract_message_contents(message):
    """
    Extract the plain text and HTML content from a Gmail message resource (format='full').
    Returns: (plain_text: str, html_text: str)
    """
    payload = message.get("payload", {}) or {}
    mime_type = payload.get("mimeType", "")
    text_content = ""
    html_content = ""

    def handle_part(part):
        nonlocal text_content, html_content
        body = part.get("body", {}) or {}
        mime = part.get("mimeType", "")
        data = body.get("data")
        if data:
            decoded = _safe_decode_base64(data)
            if mime == "text/plain":
                text_content += decoded
            elif mime == "text/html":
                html_content += decoded
        for p in part.get("parts", []) or []:
            handle_part(p)

    if payload.get("parts"):
        for part in payload.get("parts"):
            handle_part(part)
    else:
        handle_part(payload)

    text_content = text_content.strip()
    html_content = html_content.strip()
    if not text_content and html_content:
        import re
        text_try = re.sub("<[^<]+?>", "", html_content)
        text_try = unescape(text_try)
        text_content = text_try.strip()

    return text_content, html_content


def has_attachments(message):
    """
    Return True if the message payload indicates attachments present.
    """
    payload = message.get("payload", {}) or {}
    parts = payload.get("parts", []) or []
    for p in parts:
        filename = p.get("filename")
        body = p.get("body", {}) or {}
        if filename and isinstance(filename, str) and filename.strip():
            return True
        if body.get("attachmentId"):
            return True
    return False


def sanitize_message_record(raw_message, keep_snippet=True):
    """
    Given the raw message resource, produce a sanitized dict with NO personal identifiers.
    We remove headers like From, To, Cc, Bcc, and Date.
    Keep only: id, snippet (optional), payload_text, payload_html, has_attachments.
    """
    msg_id = raw_message.get("id")
    snippet = raw_message.get("snippet") if keep_snippet else None
    text, html = extract_message_contents(raw_message)
    return {
        "id": msg_id,
        "snippet": snippet,
        "payload_text": text,
        "payload_html": html,
        "has_attachments": has_attachments(raw_message),
    }
