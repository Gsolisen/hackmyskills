"""Tests for the hms CLI entry point (FOUND-01)."""
from typer.testing import CliRunner
from hms.cli import app

runner = CliRunner()


def test_hms_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "HackMySkills" in result.output


def test_hms_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_hms_no_args_shows_dashboard():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "HackMySkills" in result.output
