from pydantic import BaseModel

from hermes.model import SoftwareMetadata
from .base import HermesCurateCommand, HermesCuratePlugin


class DoNothingCurateSettings(BaseModel):
    pass


class DoNothingCuratePlugin(HermesCuratePlugin):
    settings_class = DoNothingCurateSettings

    def __call__(self, command: HermesCurateCommand, metadata: SoftwareMetadata) -> SoftwareMetadata:
        return metadata
