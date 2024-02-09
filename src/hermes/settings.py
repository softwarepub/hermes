# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Sophie Kernchen

from pydantic import BaseModel
import toml
import pathlib
from typing import Any, Dict, Tuple, Type

from pydantic.fields import FieldInfo


from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class HarvestCff(BaseModel):
    enable_validation: bool = True


class HarvestSettings(BaseModel):
    sources: list[str] = []
    cff: HarvestCff = HarvestCff()
    cff_validate: bool = True

    harvester: Dict = {}


class DepositTargetSettings(BaseModel):
    site_url: str = ""

    communities: list[str] = None
    access_right: str = None
    embargo_date: str = None
    access_conditions: str = None
    api_paths: Dict = {}

    record_id: int = None
    doi: str = None


class DepositSettings(BaseModel):
    target: str = ""
    invenio: DepositTargetSettings = DepositTargetSettings()
    invenio_rdm: DepositTargetSettings = DepositTargetSettings()

    file: Dict = {}

    def __getattr__(self, item):
        self.__pydantic_extra__ = {item: {}}


class PostprocessSettings(BaseModel):
    execute: list = []


class HermesSettings(BaseSettings):

    model_config = SettingsConfigDict(env_file_encoding='utf-8', extra='allow')

    harvest: HarvestSettings = HarvestSettings()
    deposit: DepositSettings = DepositSettings()
    postprocess: PostprocessSettings = PostprocessSettings()

    hermes: Dict = {}
    file: Dict = {}
    filename: pathlib.Path = "hermes.toml"
    logging: Dict = {}
    site_url: str = ""

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: Type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            TomlConfigSettingsSource(settings_cls, "hermes.toml"),
            env_settings,
            file_secret_settings,
        )

    def __getattr__(self, item, *args):
        self.__pydantic_extra__ = {item: {}}


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
