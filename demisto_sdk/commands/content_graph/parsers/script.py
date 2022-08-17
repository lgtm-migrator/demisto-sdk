import re
from pathlib import Path
from typing import List

from demisto_sdk.commands.content_graph.constants import ContentTypes, Rel
import demisto_sdk.commands.content_graph.parsers.integration_script as integration_script

EXECUTE_CMD_PATTERN = re.compile(r"execute_?command\(['\"](\w+)['\"].*", re.IGNORECASE)


class ScriptParser(integration_script.IntegrationScriptParser):
    def __init__(self, path: Path, pack_marketplaces: List[str]) -> None:
        super().__init__(path, pack_marketplaces)
        print(f'Parsing {self.content_type} {self.object_id}')
        self.docker_image = self.yml_data.get('dockerimage', '')
        self.type = self.yml_data.get('subtype') or self.yml_data.get('type')
        self.tags = self.yml_data.get('tags', [])
        if self.type == 'python':
            self.type += '2'

        self.connect_to_dependencies()
        self.connect_to_tests()

    @property
    def content_type(self) -> ContentTypes:
        return ContentTypes.SCRIPT

    def connect_to_dependencies(self) -> None:
        for cmd in self.get_depends_on():
            self.add_dependency(cmd)

        for cmd in self.get_command_executions():
            self.add_dependency(cmd)

    def get_depends_on(self) -> List[str]:
        depends_on: List[str] = self.yml_data.get('dependson', {}).get('must', [])
        return list({cmd.split('|')[-1] for cmd in depends_on})

    def get_code(self) -> str:
        if self.is_unified or self.yml_data.get('script') not in ['-', '']:
            return self.yml_data.get('script')
        return self.unifier.get_script_or_integration_package_data()[1]

    def get_command_executions(self) -> List[str]:
        return set(EXECUTE_CMD_PATTERN.findall(self.get_code()))
