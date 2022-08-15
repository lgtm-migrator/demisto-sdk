
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from demisto_sdk.commands.content_graph.constants import ContentTypes, Relationship


class ContentGraphInterface(ABC):
    @abstractmethod
    def create_indexes_and_constraints(self) -> None:
        pass

    @abstractmethod
    def create_nodes(self, nodes: Dict[ContentTypes, List[Dict[str, Any]]]) -> None:
        pass

    @abstractmethod
    def create_relationships(self, relationships: Dict[Relationship, List[Dict[str, Any]]]) -> None:
        pass

    @abstractmethod
    def create_pack_dependencies(self) -> None:
        pass

    @abstractmethod
    def run_single_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        pass
    
    @abstractmethod
    def get_all_content_items(self, marketplace: str) -> dict:
        pass
