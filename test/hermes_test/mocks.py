# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: CC0-1.0

# SPDX-FileContributor: Stephan Druskat

from unittest import mock
import typing as t

import click


def mock_command(name: str) -> t.Tuple[mock.Mock, click.Command]:
    func = mock.Mock(return_value=name)
    return func, click.command(name)(func)
