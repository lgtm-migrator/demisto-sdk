import tempfile

import pytest

from demisto_sdk.commands.common.mardown_lint import has_markdown_lint_errors


@pytest.mark.parametrize('file_content, expected_error', [
    ('##Hello', 'MD018: No space present after the hash character on a possible Atx Heading'), (
        """
## Unreleased

   * Feature1
* feature2""", 'MD005: Inconsistent indentation for list items at the same level'
    ), ("""## Header
    next line""", "MD022: Headings should be surrounded by blank lines."),
    ("<p>something</p>", 'MD033: Inline HTML [Element: p] (no-inline-html)')
])
def test_markdown_validations(file_content, expected_error, mocker):
    click_mock = mocker.patch("click.secho")
    with tempfile.NamedTemporaryFile(suffix=".md") as temp:
        temp.write(file_content.encode())
        temp.flush()
        assert has_markdown_lint_errors(temp.name)
        assert expected_error in click_mock.call_args.args[0]
