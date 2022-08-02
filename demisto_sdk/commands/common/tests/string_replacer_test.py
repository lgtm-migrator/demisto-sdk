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
            (f'{STRING_REPLACER_PREFIX}hello world', {'hello': ''}, ' world'),
            (f'hello world', {'hello': 'hey'}, 'hello world'),
            (f'hello world', {}, 'hello world'),
            (f'{STRING_REPLACER_PREFIX}hello world', {}, f'{STRING_REPLACER_PREFIX}hello world'),
            (f'hello {STRING_REPLACER_PREFIX}world', {'world': 'planet'}, 'hello planet'),
            (f'{STRING_REPLACER_PREFIX}hello {STRING_REPLACER_PREFIX}world', {'hello': 'hey',
                                                                              'world': 'planet'}, 'hey planet'),
            # todo more complicated tests, multiple replacements, recursion
    )
)
def test_replace(text: str, replacements: dict, expected: str):
    with StringReplacerContextManager(replacements):
        assert StringReplacer.replace(text) == expected


def test_default_dict_values_exclude_prefix():
    for key in StringReplacer.DICTIONARY:
        assert not key.startswith(STRING_REPLACER_PREFIX)
        assert (re.escape(STRING_REPLACER_PREFIX + key) in StringReplacer.REPLACEMENTS)


def test_default_replacement_values_include_prefix():
    for key in StringReplacer.REPLACEMENTS:
        assert key.startswith(re.escape(STRING_REPLACER_PREFIX))
