import os
import subprocess
from pathlib import Path
from typing import Optional
from unittest import mock

import pytest
import shellingham
import typer
import typer.completion
from typer.main import solve_typer_info_defaults, solve_typer_info_help
from typer.models import TyperInfo
from typer.testing import CliRunner

import click.exceptions

runner = CliRunner()


def test_optional():
    app = typer.Typer()

    @app.command()
    def opt(user: Optional[str] = None):
        if user:
            typer.echo(f"User: {user}")
        else:
            typer.echo("No user")

    result = runner.invoke(app)
    assert result.exit_code == 0
    assert "No user" in result.output

    result = runner.invoke(app, ["--user", "Camila"])
    assert result.exit_code == 0
    assert "User: Camila" in result.output


def test_no_type():
    app = typer.Typer()

    @app.command()
    def no_type(user):
        typer.echo(f"User: {user}")

    result = runner.invoke(app, ["Camila"])
    assert result.exit_code == 0
    assert "User: Camila" in result.output


def test_help_from_info():
    # Mainly for coverage/completeness
    value = solve_typer_info_help(TyperInfo())
    assert value is None


def test_defaults_from_info():
    # Mainly for coverage/completeness
    value = solve_typer_info_defaults(TyperInfo())
    assert value


def test_install_invalid_shell():
    app = typer.Typer()

    @app.command()
    def main():
        typer.echo("Hello World")

    with mock.patch.object(
        shellingham, "detect_shell", return_value=("xshell", "/usr/bin/xshell")
    ):
        result = runner.invoke(app, ["--install-completion"])
        assert "Shell xshell is not supported." in result.stdout
    result = runner.invoke(app)
    assert "Hello World" in result.stdout


def test_callback_too_many_parameters():
    app = typer.Typer()

    def name_callback(ctx, param, val1, val2):
        pass  # pragma: nocover

    @app.command()
    def main(name: str = typer.Option(..., callback=name_callback)):
        pass  # pragma: nocover

    with pytest.raises(click.exceptions.ClickException) as exc_info:
        runner.invoke(app, ["--name", "Camila"])
    assert (
        exc_info.value.message == "Too many CLI parameter callback function parameters"
    )


def test_callback_2_untyped_parameters():
    app = typer.Typer()

    def name_callback(ctx, value):
        typer.echo(f"info name is: {ctx.info_name}")
        typer.echo(f"value is: {value}")

    @app.command()
    def main(name: str = typer.Option(..., callback=name_callback)):
        typer.echo("Hello World")

    result = runner.invoke(app, ["--name", "Camila"])
    assert "info name is: main" in result.stdout
    assert "value is: Camila" in result.stdout


def test_callback_3_untyped_parameters():
    app = typer.Typer()

    def name_callback(ctx, param, value):
        typer.echo(f"info name is: {ctx.info_name}")
        typer.echo(f"param name is: {param.name}")
        typer.echo(f"value is: {value}")

    @app.command()
    def main(name: str = typer.Option(..., callback=name_callback)):
        typer.echo("Hello World")

    result = runner.invoke(app, ["--name", "Camila"])
    assert "info name is: main" in result.stdout
    assert "param name is: name" in result.stdout
    assert "value is: Camila" in result.stdout


def test_completion_untyped_parameters():
    file_path = Path(__file__).parent / "assets/completion_no_types.py"
    result = subprocess.run(
        ["coverage", "run", str(file_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        env={
            **os.environ,
            "_COMPLETION_NO_TYPES.PY_COMPLETE": "complete_zsh",
            "_TYPER_COMPLETE_ARGS": "completion_no_types.py --name Sebastian --name Ca",
            "_TYPER_COMPLETE_TESTING": "True",
        },
    )
    assert "info name is: completion_no_types.py" in result.stderr
    assert "args is: ['--name', 'Sebastian', '--name']" in result.stderr
    assert "incomplete is: Ca" in result.stderr
    assert '"Camila":"The reader of books."' in result.stdout
    assert '"Carlos":"The writer of scripts."' in result.stdout
    assert '"Sebastian":"The type hints guy."' in result.stdout


def test_completion_untyped_parameters_different_order_correct_names():
    file_path = Path(__file__).parent / "assets/completion_no_types_order.py"
    result = subprocess.run(
        ["coverage", "run", str(file_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        env={
            **os.environ,
            "_COMPLETION_NO_TYPES_ORDER.PY_COMPLETE": "complete_zsh",
            "_TYPER_COMPLETE_ARGS": "completion_no_types_order.py --name Sebastian --name Ca",
            "_TYPER_COMPLETE_TESTING": "True",
        },
    )
    assert "info name is: completion_no_types_order.py" in result.stderr
    assert "args is: ['--name', 'Sebastian', '--name']" in result.stderr
    assert "incomplete is: Ca" in result.stderr
    assert '"Camila":"The reader of books."' in result.stdout
    assert '"Carlos":"The writer of scripts."' in result.stdout
    assert '"Sebastian":"The type hints guy."' in result.stdout


def test_autocompletion_too_many_parameters():
    app = typer.Typer()

    def name_callback(ctx, args, incomplete, val2):
        pass  # pragma: nocover

    @app.command()
    def main(name: str = typer.Option(..., autocompletion=name_callback)):
        pass  # pragma: nocover

    with pytest.raises(click.exceptions.ClickException) as exc_info:
        runner.invoke(app, ["--name", "Camila"])
    assert exc_info.value.message == "Invalid autocompletion callback parameters: val2"
