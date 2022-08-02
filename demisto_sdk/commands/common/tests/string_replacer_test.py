import re

import pytest

from demisto_sdk.commands.common.string_replacer import (
    STRING_REPLACER_PREFIX,
    StringReplacer,
)


class StringReplacerContextManager:
    def __init__(self, replacement_dict: dict[str, str]):
        self.dict_ = replacement_dict

    def __enter__(self):
        self.last_dict = StringReplacer.DICTIONARY
        self.mock(self.dict_)

    def __exit__(self, *args):
        self.mock(self.last_dict)
        self.last_dict = StringReplacer.DICTIONARY

    @staticmethod
    def mock(dict_: dict[str, str]):
        StringReplacer.DICTIONARY = dict_
        StringReplacer.REPLACEMENTS = {
            re.escape(STRING_REPLACER_PREFIX + k): v for k, v in dict_.items()
        }
        StringReplacer.PATTERN = re.compile(
            '|'.join(StringReplacer.REPLACEMENTS.keys())
        )


@pytest.mark.parametrize(
    'text,replacements,expected',
    (
            (f'{STRING_REPLACER_PREFIX}hello world', {'hello': 'hey'}, 'hey world'),
            (f'{STRING_REPLACER_PREFIX}hello world', {'what\'s up': 'hey'}, f'{STRING_REPLACER_PREFIX}hello world'),
            (f'hello world', {'hello': 'hey'}, 'hello world'),
            (f'hello world', {}, 'hello world'),
            (f'hello world', {'world': 'planet'}, 'hello world'),
    ))
def test_replace(text: str, replacements: dict, expected: str):
    with StringReplacerContextManager(replacements):
        assert StringReplacer.replace(text) == expected
