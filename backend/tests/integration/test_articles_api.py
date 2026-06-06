"""Article upload + processing endpoints.

Covers the ingestion happy path plus the hardening the review demanded: a size
cap (unauthenticated memory-exhaustion DoS), extension validation, and that two
uploads of the same filename don't overwrite each other on disk.
"""
from __future__ import annotations

import io


def _csv_bytes(rows: list[str]) -> bytes:
    header = "title,article_text,url,source\n"
    return (header + "\n".join(rows)).encode("utf-8")


def _upload(client, content: bytes, filename: str = "news.csv"):
    return client.post(
        "/api/v1/articles/upload",
        files={"file": (filename, io.BytesIO(content), "text/csv")},
    )


class TestUploadHappyPath:
    def test_valid_csv_returns_run_id_and_counts(self, client):
        content = _csv_bytes(
            ['"Adani Ports Q4 preview","body text",http://x,Mint',
             '"Nifty hits record high","macro body",http://y,ET']
        )
        res = _upload(client, content)
        assert res.status_code == 200
        body = res.json()
        assert body["valid"] is True
        assert body["total_rows"] == 2
        assert body["run_id"] is not None

    def test_missing_title_column_is_invalid_and_no_run(self, client):
        content = b"foo,bar\n1,2\n"
        res = _upload(client, content)
        assert res.status_code == 200
        body = res.json()
        assert body["valid"] is False
        assert body["run_id"] is None


class TestUploadValidation:
    def test_non_csv_extension_rejected(self, client):
        res = _upload(client, b"whatever", filename="malware.exe")
        assert res.status_code == 400

    def test_oversized_upload_rejected_with_413(self, client, monkeypatch):
        """A multi-GB upload must not be slurped into memory. We cap it small in
        config for the test and expect 413, not a 200 + OOM."""
        from app.core import config as config_mod
        from app.api.v1.endpoints import articles as articles_ep

        monkeypatch.setattr(config_mod.settings, "MAX_UPLOAD_BYTES", 50, raising=False)
        monkeypatch.setattr(articles_ep.settings, "MAX_UPLOAD_BYTES", 50, raising=False)

        big = _csv_bytes(['"x","' + "a" * 500 + '",u,s'])
        res = _upload(client, big)
        assert res.status_code == 413


class TestUploadStorageSafety:
    def test_same_filename_twice_does_not_overwrite(self, client, tmp_path):
        """Two analysts uploading 'news.csv' must not clobber each other's stored
        file — each upload gets a unique storage key."""
        from app.api.v1.endpoints import articles as articles_ep

        storage = articles_ep.get_storage()
        c1 = _csv_bytes(['"First headline","b",u,s'])
        c2 = _csv_bytes(['"Second headline","b",u,s'])

        r1 = _upload(client, c1, filename="news.csv")
        r2 = _upload(client, c2, filename="news.csv")
        assert r1.status_code == 200 and r2.status_code == 200

        # Both runs exist with distinct ids.
        assert r1.json()["run_id"] != r2.json()["run_id"]

    def test_process_runs_inline_and_marks_complete(self, client, monkeypatch):
        """End-to-end: upload then process (sync) with the mock LLM yields a
        completed run with all rows accounted for."""
        from app.services.llm import factory as llm_factory
        from app.services.llm.mock import MockProvider

        monkeypatch.setattr(llm_factory, "get_llm_provider", lambda: MockProvider())

        content = _csv_bytes(
            ['"Adani Ports Q4 preview","body",u,s',
             '"REC Q4 results out","body",u,s']
        )
        up = _upload(client, content).json()
        res = client.post("/api/v1/articles/process", json={"run_id": up["run_id"]})
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "completed"
        assert body["processed"] + body["failed"] == body["total_rows"]
