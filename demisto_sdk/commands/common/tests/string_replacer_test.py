import re

import pytest

from demisto_sdk.commands.common.constants import MarketplaceVersions
from demisto_sdk.commands.common.string_replacer import (
    STRING_REPLACER_PREFIX, StringReplacer)


class StringReplacerMock(StringReplacer):
    def __init__(self, replacement_dict: dict[str, str]):
        super().__init__(MarketplaceVersions.XSOAR)  # does not matter, as the dictionary is overwritten
        self.dictionary = replacement_dict
        self._replacements = {
            re.escape(STRING_REPLACER_PREFIX + k if not k.startswith(STRING_REPLACER_PREFIX) else k): v
            for k, v in self.dictionary.items()
        }
        self._pattern = re.compile('|'.join(self._replacements.keys()))


@pytest.mark.parametrize('marketplace', MarketplaceVersions)
def test_sanity(marketplace: MarketplaceVersions):
    """
    Given   a marketplace value
    When    calling replace on a string that includes the first replaceable value in the dictionary file
    Then    make sure the replacer does replace the string
    """
    replacer = StringReplacer(marketplace)
    key, value = next(iter(replacer.dictionary.items()))
    assert replacer.replace(f'foo{STRING_REPLACER_PREFIX}{key}bar') == f'foo{value}bar'


@pytest.mark.parametrize('marketplace', MarketplaceVersions)
def test_dictionary_loading(marketplace: MarketplaceVersions):
    """
    Given   a marketplace value
    When    calling replace on a string that includes the first replaceable value in the dictionary file
    Then    make sure the dictionary is not empty
    """
    replacer = StringReplacer(marketplace)
    assert replacer.dictionary


@pytest.mark.parametrize(
    'text,dictionary,expected',
    (
            (f'{STRING_REPLACER_PREFIX}hello world', {'hello': 'hey'}, 'hey world'),
            (f'{STRING_REPLACER_PREFIX}hello world', {'what\'s up': 'hey'}, f'{STRING_REPLACER_PREFIX}hello world'),
            (f'{STRING_REPLACER_PREFIX}hello world', {'hello': ''}, ' world'),
            ('hello world', {'hello': 'hey'}, 'hello world'),
            ('hello world', {}, 'hello world'),
            (f'{STRING_REPLACER_PREFIX}hello world', {}, f'{STRING_REPLACER_PREFIX}hello world'),
            (f'hello {STRING_REPLACER_PREFIX}world', {'world': 'planet'}, 'hello planet'),
            (f'{STRING_REPLACER_PREFIX}hello {STRING_REPLACER_PREFIX}world', {'hello': 'hey',
                                                                              'world': 'planet'}, 'hey planet'),
            (f'{STRING_REPLACER_PREFIX}1', {'1': f'{STRING_REPLACER_PREFIX}2', f'{STRING_REPLACER_PREFIX}2': '3'}, '3')
    )
)
def test_replace(text: str, dictionary: dict, expected: str):
    assert StringReplacerMock(dictionary).replace(text) == expected


@pytest.mark.parametrize('marketplace', MarketplaceVersions)
def test_default_dict_values_exclude_prefix(marketplace: MarketplaceVersions):
    replacer = StringReplacer(marketplace)
    for key in replacer.dictionary:
        assert not key.startswith(STRING_REPLACER_PREFIX)
        assert not key.startswith(re.escape(STRING_REPLACER_PREFIX))

        prefix_free_key = key.removeprefix(STRING_REPLACER_PREFIX)
        assert (re.escape(STRING_REPLACER_PREFIX + prefix_free_key) in replacer._replacements)


@pytest.mark.parametrize('marketplace', MarketplaceVersions)
def test_default_replacement_values_include_prefix(marketplace: MarketplaceVersions):
    for key in StringReplacer(marketplace)._replacements:
        assert key.startswith(re.escape(STRING_REPLACER_PREFIX))
        assert not key.startswith(2 * re.escape(STRING_REPLACER_PREFIX))  # avoid double prefix
