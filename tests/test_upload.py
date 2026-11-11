import io

import pytest

import config
from app import app
from services.email_parser import parse_upload, split_txt_emails, parse_eml, ParseError

client = app.test_client()

EML = (b"From: Alice <alice@example.invalid>\r\nSubject: =?utf-8?B?RlJFRSBnaWZ0?=\r\n"
       b"MIME-Version: 1.0\r\nContent-Type: multipart/alternative; boundary=XX\r\n\r\n"
       b"--XX\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nClick here to claim.\r\n"
       b"--XX\r\nContent-Type: text/html; charset=utf-8\r\n\r\n<p>HTML <b>part</b></p>\r\n--XX--\r\n")


def test_txt_single():
    out = parse_upload("a.txt", b"Subject: Hi\nFrom: x@y.invalid\n\nHello there")
    assert len(out) == 1 and out[0]["subject"] == "Hi" and out[0]["sender"] == "x@y.invalid"


def test_txt_multiple_with_delimiter():
    raw = f"one free\n{config.EMAIL_DELIMITER}\n\ntwo\n{config.EMAIL_DELIMITER}\n   \n{config.EMAIL_DELIMITER}\nthree".encode()
    assert [e["text"] for e in parse_upload("m.txt", raw)] == ["one free", "two", "three"]


def test_txt_crlf_and_utf8_bom_and_utf16():
    assert parse_upload("a.txt", "\ufeffhello\r\nfree".encode("utf-8"))[0]["text"] == "hello\nfree"
    assert parse_upload("a.txt", "héllo free".encode("utf-16"))[0]["text"] == "héllo free"
    assert parse_upload("a.txt", "café".encode("cp1252"))[0]["text"] == "café"


def test_empty_binary_and_wrong_extension():
    for name, raw in [("a.txt", b""), ("a.txt", b"   \n  "), ("a.txt", b"\x00\x01\x02bin"),
                      ("a.exe", b"hi"), ("noext", b"hi"), ("", b"hi")]:
        with pytest.raises(ParseError):
            parse_upload(name, raw)


def test_oversized():
    with pytest.raises(ParseError):
        parse_upload("a.txt", b"x" * (config.MAX_UPLOAD_BYTES + 1))


def test_too_many_emails():
    raw = (config.EMAIL_DELIMITER + "\nx\n") * (config.MAX_EMAILS_PER_FILE + 5)
    with pytest.raises(ParseError):
        split_txt_emails(raw)


def test_eml_multipart_and_encoded_subject():
    e = parse_eml(EML)
    assert e["subject"] == "FREE gift" and "alice@example.invalid" in e["sender"]
    assert "Click here to claim." in e["text"] and "HTML" not in e["text"]


def test_eml_html_only_is_converted_to_text():
    raw = b"Subject: s\r\nContent-Type: text/html; charset=utf-8\r\n\r\n<script>x()</script><p>Win <b>big</b></p>"
    t = parse_eml(raw)["text"]
    assert "Win big" in t and "x()" not in t


def test_eml_malformed_or_empty():
    with pytest.raises(ParseError):
        parse_eml(b"")
    with pytest.raises(ParseError):
        parse_eml(b"   \r\n")


def test_eml_unknown_charset_does_not_crash():
    raw = b"Subject: s\r\nContent-Type: text/plain; charset=made-up-9\r\n\r\nfree stuff"
    try:
        out = parse_eml(raw)
        assert "free" in out["text"]
    except ParseError:
        pass


def test_upload_endpoint_ok_and_errors():
    r = client.post("/api/upload", data={"file": (io.BytesIO(b"free win"), "a.txt")},
                    content_type="multipart/form-data")
    assert r.status_code == 200 and r.get_json()["count"] == 1
    r = client.post("/api/upload", data={}, content_type="multipart/form-data")
    assert r.status_code == 400
    r = client.post("/api/upload", data={"file": (io.BytesIO(b"x"), "a.pdf")},
                    content_type="multipart/form-data")
    assert r.status_code == 400 and "Only .txt" in r.get_json()["error"]
    r = client.post("/api/upload", data={"file": (io.BytesIO(EML), "m.eml")},
                    content_type="multipart/form-data")
    assert r.status_code == 200
    big = io.BytesIO(b"x" * (config.MAX_UPLOAD_BYTES + 100))
    r = client.post("/api/upload", data={"file": (big, "big.txt")}, content_type="multipart/form-data")
    assert r.status_code in (400, 413)


def test_api_invalid_requests():
    assert client.post("/api/scan", data="not json", content_type="text/plain").status_code == 400
    assert client.post("/api/scan", json={}).status_code == 400
    assert client.post("/api/scan", json={"text": "x", "threshold": 99}).status_code == 400
    assert client.post("/api/scan", json={"text": "x", "engine": "z"}).status_code == 400
    assert client.post("/api/scan/batch", json={"emails": []}).status_code == 400
    assert client.post("/api/scan/batch", json={"emails": [1]}).status_code == 400
    assert client.post("/api/simulate/xyz", json={"text": "a"}).status_code == 404
    assert client.get("/api/nope").status_code == 404
    assert client.get("/generated/../config.py").status_code == 404
