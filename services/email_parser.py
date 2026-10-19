"""Safe parsing of pasted text, .txt files (one or many emails) and .eml files.

Nothing is executed, no attachment is opened and no URL is fetched.
"""
import re
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser

import config


class ParseError(ValueError):
    """Raised for problems the user should be told about."""


def decode_bytes(raw):
    """Decode uploaded bytes. Supports UTF-8 (with/without BOM), UTF-16 with BOM, cp1252."""
    if not raw:
        raise ParseError("The file is empty.")
    if b"\x00" in raw and not raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise ParseError("The file looks binary, not text. Unsupported encoding.")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError:
            raise ParseError("Could not decode the UTF-16 file.")
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ParseError("Unsupported text encoding. Please save the file as UTF-8.")


def _headers_from_text(text):
    """Pick Subject:/From: out of the first lines of a pasted email (display only)."""
    subject = sender = ""
    for line in text.splitlines()[:12]:
        low = line.lower()
        if low.startswith("subject:") and not subject:
            subject = line[8:].strip()
        elif low.startswith("from:") and not sender:
            sender = line[5:].strip()
    return subject, sender


def split_txt_emails(text):
    """Split on lines that contain exactly EMAIL_DELIMITER; skip empty parts."""
    parts, current = [], []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.strip() == config.EMAIL_DELIMITER:
            parts.append("\n".join(current))
            current = []
        else:
            current.append(line)
    parts.append("\n".join(current))
    emails = []
    for part in parts:
        body = part.strip("\n")
        if body.strip():
            subject, sender = _headers_from_text(body)
            emails.append({"subject": subject, "sender": sender, "text": body})
    if len(emails) > config.MAX_EMAILS_PER_FILE:
        raise ParseError(f"Too many emails in one file (limit {config.MAX_EMAILS_PER_FILE}).")
    return emails


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.chunks = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.chunks.append(data)


def _html_to_text(html):
    p = _TextExtractor()
    p.feed(html)
    return re.sub(r"\n{3,}", "\n\n", "".join(p.chunks)).strip()


def parse_eml(raw):
    """Parse a standard .eml file into subject, sender and readable plain text."""
    if not raw or not raw.strip():
        raise ParseError("The file is empty.")
    try:
        msg = BytesParser(policy=policy.default).parsebytes(raw)
    except Exception:
        raise ParseError("The .eml file could not be parsed.")
    subject = str(msg.get("subject", "") or "")
    sender = str(msg.get("from", "") or "")
    if not subject and not sender and not msg.is_multipart() and not msg.get_payload():
        raise ParseError("No readable email headers or body were found in this .eml file.")
    body = ""
    try:
        part = msg.get_body(preferencelist=("plain",))
        if part is not None:
            body = part.get_content()
        else:
            part = msg.get_body(preferencelist=("html",))
            if part is not None:
                body = _html_to_text(part.get_content())
            elif not msg.is_multipart():
                body = msg.get_content() if msg.get_content_maintype() == "text" else ""
    except (LookupError, UnicodeDecodeError, KeyError):
        raise ParseError("The email body uses an unsupported character encoding.")
    body = (body or "").strip()
    if not (subject or sender or body):
        raise ParseError("No readable text was found in this .eml file.")
    text = f"Subject: {subject}\nFrom: {sender}\n\n{body}".strip()
    return {"subject": subject, "sender": sender, "text": text}


def parse_upload(filename, raw):
    """Entry point for uploads. Returns a list of {subject, sender, text}."""
    if not filename:
        raise ParseError("No file name was provided.")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("txt", "eml"):
        raise ParseError("Only .txt and .eml files are supported.")
    if len(raw) > config.MAX_UPLOAD_BYTES:
        raise ParseError(f"File too large (limit {config.MAX_UPLOAD_BYTES // 1024} KB).")
    if ext == "eml":
        return [parse_eml(raw)]
    emails = split_txt_emails(decode_bytes(raw))
    if not emails:
        raise ParseError("The file contains no email text.")
    return emails
