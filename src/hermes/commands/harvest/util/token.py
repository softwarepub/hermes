# SPDX-FileCopyrightText: 2025 OFFIS e.V.
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Ferenz
# SPDX-FileContributor: Aida Jafarbigloo

import toml
import base64


def load_token_from_toml(config_path: str = "hermes.toml") -> str:
    """
    Loads and decodes the token from the HERMES TOML configuration file.

    Args:
        config_path (str): Path to the TOML config file.

    Returns:
        str: The decoded token.
    """
    with open(config_path, "r") as f:
        config = toml.load(f)
    
    encoded_token = config.get('harvest', {}).get('token')
    if encoded_token:
        return base64.b64decode(encoded_token.encode()).decode()
    else:
        return None
