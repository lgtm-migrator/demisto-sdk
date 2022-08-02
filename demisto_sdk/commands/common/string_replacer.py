import re
from pathlib import Path

from demisto_sdk.commands.common.constants import MarketplaceVersions
from demisto_sdk.commands.common.handlers import JSON_Handler

json = JSON_Handler()

STRING_REPLACER_PREFIX = 'STR$'


MARKETPLACE_TO_DICTIONARY_FILE = {
    MarketplaceVersions.XSOAR: Path(__file__).absolute().parent / 'string_replacer_values_xsoar.json',
    MarketplaceVersions.MarketplaceV2: Path(__file__).absolute().parent / 'string_replacer_values_marketplacev2.json'
}


class StringReplacer:
    def __init__(self, marketplace: MarketplaceVersions):
        with open(MARKETPLACE_TO_DICTIONARY_FILE[marketplace]) as f:
            self.dictionary = json.load(f)

        self._replacements = {re.escape(STRING_REPLACER_PREFIX + k): v for k, v in self.dictionary.items()}
        self._pattern = re.compile('|'.join(self._replacements.keys()))

    def replace(self, text: str):
        if not self.dictionary:
            return text

        return self._pattern.sub(
            lambda m: self._replacements[re.escape(m.group(0))], text
        )
