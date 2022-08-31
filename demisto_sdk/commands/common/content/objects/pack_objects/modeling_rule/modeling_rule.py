import shutil
import re
from typing import List, Optional, Union

import demisto_client
from wcmatch.pathlib import Path
from pprint import pformat

import demisto_sdk.commands.common.content.errors as exc
from demisto_sdk.commands.common.constants import MODELING_RULE, FileType
from demisto_sdk.commands.common.content.objects.pack_objects.abstract_pack_objects.yaml_unify_content_object import \
    YAMLContentUnifiedObject
from demisto_sdk.commands.common.tools import generate_xsiam_normalized_name


class MRule:
    RULE_HEADER_REGEX = r"\[MODEL:\sdataset=(?P<dataset>\w+)(?=,\smodel=(?P<datamodel>\w+)])"
    RULE_FIELDS_REGEX = r"XDM\.[\w\.]+(?=\s*?=\s*?\w+)"

    def __init__(self, rule_text: str):
        self.rule_text = rule_text
        self._dataset = ""
        self._datamodel = ""
        self._fields: List[str] = []

    @property
    def dataset(self) -> str:
        if not self._dataset:
            match = re.match(self.RULE_HEADER_REGEX, self.rule_text)
            if match:
                self.dataset = match.groupdict().get('dataset', '')
                if not self._dataset:
                    raise ValueError(f"could not parse the dataset from the rule text: \"{self.rule_text}\"")
                if not self._datamodel:
                    dm = match.groupdict().get('datamodel')
                    if dm:
                        self.datamodel = dm
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        self._dataset = value

    @property
    def datamodel(self) -> str:
        if not self._datamodel:
            match = re.match(self.RULE_HEADER_REGEX, self.rule_text)
            if match:
                self.datamodel = match.groupdict().get('datamodel', '')
                if not self._datamodel:
                    raise ValueError(f"could not parse the datamodel from the rule text: \"{self.rule_text}\"")
                if not self._dataset:
                    ds = match.groupdict().get('dataset')
                    if ds:
                        self.dataset = ds
        return self._datamodel

    @datamodel.setter
    def datamodel(self, value):
        self._datamodel = value

    @property
    def fields(self):
        if not self._fields:
            uniq_fields = set(re.findall(self.RULE_FIELDS_REGEX, self.rule_text))
            self.fields = uniq_fields
            if not self._fields:
                raise ValueError(f"could not parse datamodel fields from the rule text: \"{self.rule_text}\"")
        return self._fields

    @fields.setter
    def fields(self, value):
        self._fields = value

    def __repr__(self) -> str:
        return pformat(
            {"datamodel": self.datamodel, "dataset": self.dataset, "fields": self.fields, "rule_text": self.rule_text}
        )


class ModelingRule(YAMLContentUnifiedObject):
    MODEL_RULE_REGEX = re.compile(
        r"(?P<header>\[MODEL:\sdataset=\w+,\smodel=\w+])\s(^(?!.*(?P=header)).+$\n)+", flags=re.MULTILINE
    )

    def __init__(self, path: Union[Path, str]):
        super().__init__(path, FileType.MODELING_RULE, MODELING_RULE)
        self._rules: List[MRule] = []

    def normalize_file_name(self) -> str:
        return generate_xsiam_normalized_name(self._path.name, MODELING_RULE)

    def upload(self, client: demisto_client.demisto_api.DefaultApi):
        """
        Upload the modeling_rule to demisto_client
        Args:
            client: The demisto_client object of the desired XSOAR machine to upload to.

        Returns:
            The result of the upload command from demisto_client
        """
        # return client.import_modeling_rules(file=self.path)
        pass

    @property
    def rules(self):
        if not self._rules:
            _rules = []
            rule_initialization_errs = []
            try:
                rules_text = self.get('rules', '')
                matches = self.MODEL_RULE_REGEX.finditer(rules_text)
                for match in matches:
                    _rules.append(MRule(match.group()))
                self.rules = _rules
            except ValueError as ve:
                rule_initialization_errs.append(ve)
            if rule_initialization_errs:
                err_msg = f"Failed to initialize ModelingRule with the following errors: {rule_initialization_errs}"
                raise exc.ContentInitializeError(self, self.path, err_msg)
        return self._rules

    @rules.setter
    def rules(self, value):
        self._rules = value

    @property
    def testdata_path(self) -> Optional[Path]:
        """Modeling rule related testdata file path.

        Returns:
            Testdata file path or None if testdata file is not found.
        """
        patterns = ["*_testdata.json"]
        return next(self.path.parent.glob(patterns=patterns, flags=IGNORECASE), None)

    def type(self):
        return FileType.MODELING_RULE

    def dump(self, dest_dir: Optional[Union[Path, str]] = None) -> List[Path]:
        created_files: List[Path] = []
        created_files.extend(super().dump(dest_dir=dest_dir))
        new_file_path = created_files[0]
        if new_file_path.name.startswith('external-'):
            copy_to_path = str(new_file_path).replace('external-', '')
        else:
            copy_to_path = f'{new_file_path.parent}/{self.normalize_file_name()}'
        shutil.copyfile(new_file_path, copy_to_path)
        return created_files
