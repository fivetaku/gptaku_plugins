from pathlib import Path

from engine import discovery


def test_discovery_reports_missing_local_miner(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(discovery, "find_endpoint_miner", lambda: None)
    result = discovery.discover("https://example.com/", state_root=tmp_path)
    assert result.state == "unavailable"
    assert result.candidates == ()
    assert "not found" in result.reason


def test_discovery_normalizes_local_miner_report(tmp_path: Path, monkeypatch) -> None:
    script = tmp_path / "skill" / "scripts" / "endpoint_miner.py"
    script.parent.mkdir(parents=True)
    script.write_text("# fake", encoding="utf-8")
    report = tmp_path / "report.json"
    report.write_text(
        '{"candidates":["https://example.com/api"],"probed":[{"url":"https://example.com/api","kind":"json"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(discovery, "find_endpoint_miner", lambda: script)
    monkeypatch.setattr(
        discovery.subprocess,
        "run",
        lambda *_args, **_kwargs: type(
            "Completed", (), {"stdout": f"report: {report}\n", "stderr": "", "returncode": 0}
        )(),
    )
    result = discovery.discover("https://example.com/", state_root=tmp_path)
    assert result.state == "probable"
    assert result.json_endpoints == 1
    assert result.report_path == str(tmp_path / "discovery" / "example.com" / "miner-report.json")
