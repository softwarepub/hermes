from unittest import mock
import typing as t

import click


def mock_command(name: str) -> t.Tuple[mock.Mock, click.Command]:
    func = mock.Mock(return_value=name)
    return func, click.command(name)(func)
