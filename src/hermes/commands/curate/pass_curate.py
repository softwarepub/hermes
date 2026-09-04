from pydantic import BaseModel

from hermes.model import SoftwareMetadata
from .base import HermesCurateCommand, HermesCuratePlugin


class PassCurateSettings(BaseModel):
    pass


class PassCuratePlugin(HermesCuratePlugin):
    settings_class = PassCurateSettings

    def __call__(self, command: HermesCurateCommand, metadata: SoftwareMetadata) -> SoftwareMetadata:
        return metadata
