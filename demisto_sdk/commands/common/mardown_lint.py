import logging
import os

import click

from demisto_sdk.commands.common.tools import run_command_os

RULES_TO_DISABLE = {
    "MD039",  # Spaces inside link text
    "MD038",  # Spaces inside code span elements"
    "MD037",  # Spaces inside emphasis markers
    "MD026",  # Trailing punctuation present in heading text. (no-trailing-punctuation)"
    'MD041',  # First line in file should be a top level heading
    'MD047',  # Each file should end with a single newline character
    'MD013',  # Line length
    'MD024',  # Multiple headings cannot contain the same content.
    'MD001',  # Heading levels should only increment by one level at a time
    'MD007',  # Unordered list indentation (this doesnt seem to work properly)
    'MD036',  # Emphasis possibly used instead of a heading element. (cant enforce a warning)
    'MD009',  # Trailing spaces
}


def has_markdown_lint_errors(file: str) -> bool:
    """

    Args:
        file: The file to run lint on

    Returns: whether errors were found in the markdown file

    """
    command = _build_command(file)
    logging.info(f'running command "{command}"')
    out, err, code = run_command_os(command, os.getcwd())

    if out:
        click.secho(out)
    if err:
        click.secho(err)
    return code != 0


def _build_command(file):
    return f'pymarkdown -d {",".join(RULES_TO_DISABLE)} scan {file}'
