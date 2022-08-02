import re

STRING_REPLACER_PREFIX = 'STR$'


class StringReplacer:
    DICTIONARY = {'foo': 'bar'}
    REPLACEMENTS = {re.escape(STRING_REPLACER_PREFIX + k): v for k, v in DICTIONARY.items()}
    PATTERN = re.compile('|'.join(REPLACEMENTS.keys()))

    @staticmethod
    def replace(text: str):
        if not StringReplacer.DICTIONARY:
            return text

        return StringReplacer.PATTERN.sub(
            lambda m: StringReplacer.REPLACEMENTS[re.escape(m.group(0))], text
        )
