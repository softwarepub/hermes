# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Sophie Kernchen
# SPDX-FileContributor: Michael Meinel

import pathlib
from typing import Any, Dict, Tuple

import toml
from pydantic.fields import FieldInfo
from pydantic_settings import PydanticBaseSettingsSource


class TomlConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A simple settings source class that loads variables from a TOML file
    at the project's root.

    Here we happen to choose to use the `env_file_encoding` from Config
    when reading `config.json`
    """
    def __init__(self, settings_cls, config_path):
        super().__init__(settings_cls)
        self.__config_path = config_path

    def get_field_value(self, field: FieldInfo, field_name: str) -> Tuple[Any, str, bool]:
        file_content_toml = toml.load(pathlib.Path(self.__config_path))
        field_value = file_content_toml.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool) -> Any:
        return value

    def __call__(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(field, field_name)
            field_value = self.prepare_field_value(field_name, field, field_value, value_is_complex)
            if field_value is not None:
                d[field_key] = field_value

        return d
