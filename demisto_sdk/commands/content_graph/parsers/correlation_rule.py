from pathlib import Path

from demisto_sdk.commands.content_graph.common import ContentType
from demisto_sdk.commands.content_graph.parsers.yaml_content_item import YAMLContentItemParser


class CorrelationRuleParser(YAMLContentItemParser, content_type=ContentType.CORRELATION_RULE):
    def __init__(self, path: Path) -> None:
        super().__init__(path)

    @property
    def object_id(self) -> str:
        return self.yml_data['global_rule_id']