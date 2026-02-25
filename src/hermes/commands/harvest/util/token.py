# SPDX-FileCopyrightText: 2026 UOL
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Ferenz
# SPDX-FileContributor: Aida Jafarbigloo

from pathlib import Path
import base64
import toml


def _load_config(config_path: str) -> dict:
    """
    Load a TOML configuration file.

    If the file exists and contains valid TOML, its content is returned as a
    dictionary. If the file does not exist or contains invalid TOML, an empty
    dictionary is returned.

    Args:
        config_path: Path to the TOML configuration file.

    Returns:
        A dictionary representing the parsed TOML content,
        or an empty dictionary if loading fails.
    """
    path = Path(config_path)
    
    # Check whether the configuration file exists
    if path.exists():
        try:
            # Open the file in read mode and parse TOML content
            with path.open("r") as f:
                return toml.load(f)
        except toml.TomlDecodeError:
            # Return empty config if TOML is malformed
            return {}
        
    # Return empty config if file does not exist
    return {}


def _save_config(config: dict, config_path: str) -> None:
    """
    Save a dictionary to a TOML configuration file.

    This function overwrites the target file if it already exists.

    Args:
        config: Dictionary containing configuration data.
        config_path: Path to the TOML configuration file.
    """
    # Open the file in write mode and dump TOML content
    with Path(config_path).open("w") as f:
        toml.dump(config, f)


def update_token_to_toml(token: str, config_path: str = "hermes.toml") -> None:
    """
    Update the token in the TOML configuration file, encoding it with base64.

    Args:
        token: The personal token key to be set.
        config_path: Path to the TOML config file.
    """
    # Encode the token using base64
    encoded_token = base64.b64encode(token.encode()).decode()
    
    # Load existing configuration (or empty dict if not present)
    config = _load_config(config_path)

    # Ensure the "harvest" section exists
    config.setdefault("harvest", {})
    
    # Store the encoded token in the "harvest" section
    config["harvest"]["token"] = encoded_token

    # Persist updated configuration back to file
    _save_config(config, config_path)


def load_token_from_toml(config_path: str = "hermes.toml") -> str | None:
    """
    Load and decode the token from the TOML configuration file.

    Args:
        config_path: Path to the TOML config file.

    Returns:
        The decoded token if present, otherwise None.
    """
    # Load configuration from file
    config = _load_config(config_path)
    
    # Safely retrieve the encoded token from nested structure
    encoded_token = config.get("harvest", {}).get("token")
    
    # Decode and return the token if available, return None if no token is stored
    return base64.b64decode(encoded_token.encode()).decode() if encoded_token else None


def remove_token_from_toml(config_path: str = "hermes.toml") -> None:
    """
    Remove the 'token' field from the 'harvest' section of the TOML file.

    Args:
        config_path: Path to the TOML config file.
    """
    # Load existing configuration
    config = _load_config(config_path)
    
    # Check whether the token exists in the "harvest" section
    if "token" in config.get("harvest", {}):
        # Delete the token entry
        del config["harvest"]["token"]
        
        # Save updated configuration back to file
        _save_config(config, config_path)
