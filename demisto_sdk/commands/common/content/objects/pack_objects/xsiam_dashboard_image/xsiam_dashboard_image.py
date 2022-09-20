from typing import Union

from wcmatch.pathlib import Path

import demisto_sdk.commands.common.content.errors as exc
from demisto_sdk.commands.common.constants import XSIAM_DASHBOARD
from demisto_sdk.commands.common.content.objects.abstract_objects import \
    GeneralObject
from demisto_sdk.commands.common.tools import generate_xsiam_normalized_name


class XSIAMDashboardImage(GeneralObject):
    def __init__(self, path: Union[Path, str]):
        super().__init__(path)

    def _deserialize(self):
        pass

    def _serialize(self, dest_dir: Path):
        pass

    @staticmethod
    def _fix_path(path: Union[Path, str]):
        """Find and validate object path is valid.

        Rules:
            1. Path exists.
            2. Path is a file.

        Returns:
            Path: valid file path.

        Raises:
            ContentInitializeError: If path not valid.
        """
        path = Path(path)
        if not (path.exists() and path.is_file()):
            raise exc.ContentInitializeError(XSIAMDashboardImage, path)

        return path

    def normalize_file_name(self) -> str:
        return generate_xsiam_normalized_name(self._path.name, XSIAM_DASHBOARD)
