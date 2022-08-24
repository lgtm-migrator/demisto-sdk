from pydantic import Field
from typing import List, Optional

from demisto_sdk.commands.content_graph.objects.content_item import ContentItem


class IncidentType(ContentItem):
    playbook: Optional[str]
    hours: int
    days: int
    weeks: int
    closure_script: Optional[str] = Field(alias='closureScript')

    def summary(self):
        return self.dict(include=['name', 'playbook', 'closureScript', 'hours', 'days', 'week'])
