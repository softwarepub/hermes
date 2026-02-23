# SPDX-FileCopyrightText: 2026 UOL
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Ferenz
# SPDX-FileContributor: Aida Jafarbigloo

from pathlib import Path
import base64
import toml


def _load_config(config_path: str) -> dict:
    path = Path(config_path)
    if path.exists():
        try:
            with path.open("r") as f:
                return toml.load(f)
        except toml.TomlDecodeError:
            return {}
    return {}


def _save_config(config: dict, config_path: str) -> None:
    with Path(config_path).open("w") as f:
        toml.dump(config, f)


def update_token_to_toml(token: str, config_path: str = "hermes.toml") -> None:
    """
    Update the token in the TOML configuration file, encoding it with base64.

    Args:
        token: The personal token key to be set.
        config_path: Path to the TOML config file.
    """
    encoded_token = base64.b64encode(token.encode()).decode()
    config = _load_config(config_path)

    config.setdefault("harvest", {})
    config["harvest"]["token"] = encoded_token

    _save_config(config, config_path)


def load_token_from_toml(config_path: str = "hermes.toml") -> str | None:
    """
    Load and decode the token from the TOML configuration file.

    Args:
        config_path: Path to the TOML config file.

    Returns:
        The decoded token if present, otherwise None.
    """
    config = _load_config(config_path)
    encoded_token = config.get("harvest", {}).get("token")
    return base64.b64decode(encoded_token.encode()).decode() if encoded_token else None


def remove_token_from_toml(config_path: str = "hermes.toml") -> None:
    """
    Remove the 'token' field from the 'harvest' section of the TOML file.

    Args:
        config_path: Path to the TOML config file.
    """
    config = _load_config(config_path)
    if "token" in config.get("harvest", {}):
        del config["harvest"]["token"]
        _save_config(config, config_path)
