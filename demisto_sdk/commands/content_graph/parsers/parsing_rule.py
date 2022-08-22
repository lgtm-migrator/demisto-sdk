from pathlib import Path

from demisto_sdk.commands.content_graph.constants import ContentTypes
from demisto_sdk.commands.content_graph.parsers.content_item import YAMLContentItemParser


class ParsingRuleParser(YAMLContentItemParser, content_type=ContentTypes.PARSING_RULE):
    def __init__(self, path: Path) -> None:
        super().__init__(path)
        print(f'Parsing {self.content_type} {self.object_id}')

    @property
    def object_id(self) -> str:
        return self.yml_data.get('id')

    @property
    def content_type(self) -> ContentTypes:
        return ContentTypes.PARSING_RULE