import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from scripts.build_local_deployment import build
from scripts.check_semifinal_package import check, check_holdings, presentation_slides
from competition.package_code import package


def test_deployment_manifest_and_minimal_files(tmp_path):
    output = tmp_path / "deployment.zip"
    build(output)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert "06_本地部署/app.py" in names
        assert "06_本地部署/部署说明.md" in names
        assert not any(".env" in n or "__pycache__" in n or "data/raw/" in n for n in names)
        manifest = json.loads(archive.read("06_本地部署/package_manifest.json"))
        for name, expected in manifest["files_sha256"].items():
            assert hashlib.sha256(archive.read("06_本地部署/" + name)).hexdigest() == expected
    with pytest.raises(FileExistsError):
        build(output)


def test_deployment_unzip_runs_both_companies_and_custom(tmp_path, monkeypatch):
    import subprocess
    import sys
    output = tmp_path / "deployment.zip"
    build(output)
    with zipfile.ZipFile(output) as archive:
        archive.extractall(tmp_path / "isolated")
    directory = tmp_path / "isolated/06_本地部署"
    code = "from src.review_session import run_review,demo_cases; import json; results=[run_review(demo_name=n) for n in demo_cases()]; assert all(r['financial']['status']=='ok' for r in results); assert run_review('产品适用于机器人')['financial']['status']=='skipped'; print('OK')"
    result = subprocess.run([sys.executable, "-I", "-c", "import sys; sys.path.insert(0," + repr(str(directory)) + ");" + code], cwd=directory, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_missing_materials_never_report_ready(tmp_path):
    result = check(tmp_path)
    assert result["status"] == "BLOCKED"
    assert any("01_统一信息表" in e for e in result["errors"])
    assert any("06_本地部署" in e for e in result["errors"])


def test_slide_limit_and_invalid_archive(tmp_path):
    p = tmp_path / "deck.pptx"
    with zipfile.ZipFile(p, "w") as archive:
        archive.writestr("ppt/presentation.xml", "<presentation/>")
        for i in range(21):
            archive.writestr(f"ppt/slides/slide{i+1}.xml", "<slide/>")
    assert presentation_slides(p) == 21
    dest = tmp_path / "07_技术题"
    dest.mkdir()
    p.rename(dest / "技术题报告.pptx")
    assert "技术题报告超过20页" in check(tmp_path)["errors"]


def test_toy_holdings_cannot_pass_final_calendar(tmp_path):
    p = tmp_path / "submission.csv"
    p.write_text("date,stock_id\n2021-01-04,C0001\n")
    with pytest.raises(ValueError):
        check_holdings(p)


def test_code_package_refuses_synthetic_or_incomplete_run(tmp_path):
    (tmp_path / "run_summary.json").write_text(json.dumps({"command": "validate", "status": "COMPLETE"}))
    with pytest.raises(ValueError, match="real prediction"):
        package(tmp_path, "unused", "unused", tmp_path / "code.zip", "Actual tools")
    assert not (tmp_path / "code.zip").exists()


def test_code_package_rejects_changed_holdings_before_tool_calls(tmp_path):
    (tmp_path / "run_summary.json").write_text(json.dumps({"command": "predict", "status": "COMPLETE", "submission_check": {"status": "VALID"}, "holdings_sha256": "wrong"}))
    (tmp_path / "submission.csv").write_text("date,stock_id\n")
    with pytest.raises(ValueError, match="changed"):
        package(tmp_path, "unused", "unused", tmp_path / "code.zip", "Actual tools")


def test_localhost_is_not_a_reviewer_online_address(tmp_path):
    assert any("localhost" in e for e in check(tmp_path, "http://127.0.0.1:8501")["errors"])


def test_official_invalid_result_blocks_submission(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from scripts import check_semifinal_package as checker
    from competition import baseline
    directory = tmp_path / "07_技术题"
    directory.mkdir()
    (directory / "submission.csv").write_text("date,stock_id\n")
    monkeypatch.setattr(checker, "check_holdings", lambda path: {"days": 1212})
    monkeypatch.setattr(baseline, "verify_data", lambda *args: None)
    monkeypatch.setattr(baseline, "official_tools", lambda path: SimpleNamespace(check=lambda *args: {"status": "INVALID"}))
    result = check(tmp_path, tools="tools.py", test="test.parquet")
    assert "官方持仓校验未通过" in result["errors"]


def test_video_dimensions_must_belong_to_one_stream(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from scripts import check_semifinal_package as checker
    (tmp_path / "04_运行视频.mp4").write_bytes(b"fixture")
    metadata = {"streams": [{"codec_type": "video", "width": 1920, "height": 400},
                             {"codec_type": "video", "width": 400, "height": 1080}],
                "format": {"duration": "10"}, "chapters": []}
    monkeypatch.setattr(checker.shutil, "which", lambda name: "/fake/ffprobe")
    monkeypatch.setattr(checker.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps(metadata)))
    assert any("低于1280" in e for e in check(tmp_path)["errors"])
