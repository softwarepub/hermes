from importlib.resources import files
import toml

from hermes.utils import hermes_user_agent

pyproject = toml.loads(files("hermes").joinpath("../../pyproject.toml").read_text())
name = pyproject["project"]["name"]
version = pyproject["project"]["version"]
homepage = pyproject["project"]["urls"]["homepage"]


def test_hermes_user_agent():
    assert hermes_user_agent == f"{name}/{version} ({homepage})"