"""Test for mirascope cli add command functions."""
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from mirascope.cli import app
from mirascope.cli.schemas import MirascopeSettings, VersionTextFile

runner = CliRunner()


def initialize_tmp_mirascope(tmp_path: Path, golden_prompt: str):
    if not golden_prompt.endswith(".py"):
        golden_prompt = f"{golden_prompt}.py"
    source_file = Path(__file__).parent / "golden" / golden_prompt
    destination_dir_prompts = tmp_path / "prompts"
    destination_dir_prompts.mkdir()
    shutil.copy(source_file, destination_dir_prompts / golden_prompt)
    destination_dir_mirascope_dir = tmp_path / ".mirascope"
    destination_dir_mirascope_dir.mkdir()
    prompt_template_path = (
        Path(__file__).parent.parent.parent.parent
        / "mirascope/cli/generic/prompt_template.j2"
    )
    shutil.copy(
        prompt_template_path, destination_dir_mirascope_dir / "prompt_template.j2"
    )


@pytest.mark.parametrize(
    "version_text_file",
    [
        VersionTextFile(current_revision=None, latest_revision=None),
        VersionTextFile(current_revision="0001", latest_revision="0001"),
    ],
)
@pytest.mark.parametrize("golden_prompt", ["simple_prompt"])
@pytest.mark.parametrize(
    "mirascope_settings",
    [
        MirascopeSettings(
            mirascope_location=".mirascope",
            auto_tag=True,
            version_file_name="version.txt",
            prompts_location="prompts",
            versions_location="versions",
        ),
        MirascopeSettings(
            mirascope_location=".mirascope",
            auto_tag=False,
            version_file_name="version.txt",
            prompts_location="prompts",
            versions_location="versions",
        ),
    ],
)
@patch("mirascope.cli.utils.get_user_mirascope_settings")
@patch("mirascope.cli.commands.add.get_user_mirascope_settings")
@patch("mirascope.cli.commands.add.get_prompt_versions")
def test_add(
    mock_get_prompt_versions: MagicMock,
    mock_get_mirascope_settings_add: MagicMock,
    mock_get_mirascope_settings: MagicMock,
    mirascope_settings: MirascopeSettings,
    golden_prompt: str,
    version_text_file: VersionTextFile,
    tmp_path: Path,
):
    """Tests that `add` adds a prompt to the specified version directory."""
    mock_get_mirascope_settings_add.return_value = mirascope_settings
    mock_get_mirascope_settings.return_value = mirascope_settings
    mock_get_prompt_versions.return_value = version_text_file
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        initialize_tmp_mirascope(Path(td), golden_prompt)
        result = runner.invoke(
            app,
            ["add", golden_prompt],
        )
        print(result.output)
        # with open(
        #     Path(td)
        #     / ".mirascope"
        #     / "versions"
        #     / golden_prompt
        #     / f"0001_{golden_prompt}.py"
        # ) as f:
        #     content = f.read()
        #     print(content)


@patch("mirascope.cli.commands.add.get_user_mirascope_settings")
def test_add_unknown_file(mock_get_mirascope_settings_add: MagicMock):
    """Tests that `add` fails when the prompt file does not exist."""
    mock_get_mirascope_settings_add.return_value = MirascopeSettings(
        mirascope_location=".mirascope",
        auto_tag=True,
        version_file_name="version.txt",
        prompts_location="prompts",
        versions_location="versions",
    )
    with pytest.raises(FileNotFoundError):
        result = runner.invoke(app, ["add", "unknown_prompt"], catch_exceptions=False)
        assert result.exit_code == 1


@patch("mirascope.cli.commands.add.check_status")
@patch("mirascope.cli.commands.add.get_user_mirascope_settings")
def test_add_no_changes(
    mock_get_mirascope_settings_add: MagicMock,
    mock_check_status: MagicMock,
):
    """Tests that `add` fails when the prompt file does not exist."""
    mock_check_status.return_value = None
    mock_get_mirascope_settings_add.return_value = MirascopeSettings(
        mirascope_location=".mirascope",
        auto_tag=True,
        version_file_name="version.txt",
        prompts_location="prompts",
        versions_location="versions",
    )
    result = runner.invoke(app, ["add", "unknown_prompt"], catch_exceptions=False)
    assert result.output.strip() == "No changes detected."
