from __future__ import annotations

from pathlib import Path


def test_gitattributes_enforces_lf_for_default_text_files() -> None:
    text = Path(".gitattributes").read_text(encoding="utf-8")

    assert "* text=auto eol=lf" in text
    assert "*.ps1 text eol=crlf" in text
    assert "*.cmd text eol=crlf" in text
    assert "*.bat text eol=crlf" in text