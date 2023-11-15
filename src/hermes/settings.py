from pydantic import BaseModel

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class HarvestCff(BaseModel):
    enable_validation: bool


class HarvestSettings(BaseModel):
    sources: list[str]
    cff: HarvestCff = HarvestCff


class DepositTargetSettings(BaseModel):
    site_url: str
    communities: list[str] = None
    access_right: str


class DepositSettings(BaseModel):
    target: str
    invenio: DepositTargetSettings = DepositTargetSettings
    invenio_rdm: DepositTargetSettings = DepositTargetSettings


class HermesSettings(BaseModel):
    harvest: HarvestSettings = HarvestSettings
    deposit: DepositSettings = DepositSettings


class Settings(BaseSettings):
    hermes: HermesSettings = HermesSettings
    model_config = SettingsConfigDict(env_prefix='hermes_')
