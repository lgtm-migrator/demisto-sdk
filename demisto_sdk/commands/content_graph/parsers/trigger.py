from pathlib import Path

from demisto_sdk.commands.content_graph.common import ContentType
from demisto_sdk.commands.content_graph.parsers.json_content_item import JSONContentItemParser


class TriggerParser(JSONContentItemParser, content_type=ContentType.TRIGGER):
    def __init__(self, path: Path) -> None:
        super().__init__(path)

        self.connect_to_dependencies()

    @property
    def object_id(self) -> str:
        return self.json_data.get('trigger_id')

    @property
    def name(self) -> str:
        return self.json_data.get('trigger_name')

    def connect_to_dependencies(self) -> None:
        """ Collects the playbook used in the trigger as a mandatory dependency.
        """
        if playbook := self.json_data.get('playbook_id'):
            self.add_dependency(playbook, ContentType.PLAYBOOK)