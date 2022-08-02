from pathlib import Path
from typing import Any, Dict, List

from demisto_sdk.commands.content_graph.constants import ContentTypes
from demisto_sdk.commands.content_graph.parsers.content_item import JSONContentItemParser


class IndicatorFieldParser(JSONContentItemParser):
    def __init__(self, path: Path, pack_marketplaces: List[str]) -> None:
        super().__init__(path, pack_marketplaces)
        print(f'Parsing {self.content_type} {self.content_item_id}')
        self.connect_to_dependencies()

    @property
    def content_type(self) -> ContentTypes:
        return ContentTypes.INDICATOR_FIELD

    def get_data(self) -> Dict[str, Any]:
        json_content_item_data = super().get_data()
        classifier_mapper_data = {
            'cliName': self.json_data.get('cliName'),
            'type': self.json_data.get('type'),
            'associatedToAll': self.json_data.get('associatedToAll'),
        }
        # todo: aliases - marketplacev2
        return json_content_item_data | classifier_mapper_data

    def connect_to_dependencies(self) -> None:
        for associated_type in set(self.json_data.get('associatedTypes') or []):
            self.add_dependency(associated_type, ContentTypes.INCIDENT_TYPE)

        for system_associated_type in set(self.json_data.get('systemAssociatedTypes') or []):
            self.add_dependency(system_associated_type, ContentTypes.INCIDENT_TYPE)

        if script := self.json_data.get('script'):
            self.add_dependency(script, ContentTypes.SCRIPT)

        if field_calc_script := self.json_data.get('fieldCalcScript'):
            self.add_dependency(field_calc_script, ContentTypes.SCRIPT)