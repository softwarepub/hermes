# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel

"""
This module provides the main entry point for the HERMES command line application.
"""
import logging
import typing as t
import pathlib
from importlib import metadata

import click

from hermes import config
from hermes.commands import workflow
from hermes.config import configure, init_logging


def log_header(header, summary=None):
    _log = config.getLogger('cli')

    dist = metadata.distribution('hermes')
    meta = dist.metadata

    if header is None:
        title = f"{dist.name} workflow ({dist.version})"

        _log.info(title)
        _log.info("=" * len(title))
        _log.info('')

        if 'Summary' in meta:
            _log.info('%s', meta['Summary'])
            _log.info('')

    else:
        _log.info("%s", header)
        if summary:
            _log.info("%s", summary)
            _log.info('')


class WorkflowCommand(click.Group):
    """
    Custom multi-command that implements

    - sub-commands in a fixed order,
    - automatic call of sub-commands, and
    - filtering of commands to be executed.
    """

    def __init__(self, *args, **kwargs) -> None:
        self._command_order = []
        super().__init__(*args, **kwargs)

    def add_command(self, cmd: click.Command, name: t.Optional[str] = None) -> None:
        """
        Overridden to ensure the order of commands is retained.
        """

        cmd_name = name or cmd.name
        if cmd_name not in self.commands:
            self._command_order.append(cmd_name)
        super().add_command(cmd, name)

    def list_commands(self, ctx: click.Context) -> t.List[str]:
        """
        Overridden to return commands in fixed order.
        """

        return self._command_order

    def invoke(self, ctx: click.Context) -> t.Any:
        """
        Invoke all sub-commands in a given order.

        If there is a flag in `ctx.params` with the name of a sub-command that evaluates to `False`,
        the command is not invoked.

        :param ctx: Context for the command.
        """

        # Get the user provided working dir from the --path option or default to current working directory.
        working_path = ctx.params.get('path').absolute()

        configure(ctx.params.get('config').absolute(), working_path)
        init_logging()
        log_header(None)

        audit_log = logging.getLogger('audit')
        audit_log.info("# Running Hermes")
        audit_log.info("Running Hermes command line in: %s", working_path)
        audit_log.debug("")
        audit_log.debug("Invoked `%s` with", ctx.invoked_subcommand or self.name)
        audit_log.debug("")
        for k, v in ctx.params.items():
            audit_log.debug("`--%s`", k)
            audit_log.debug(":   `%s`", v)
            audit_log.debug("")

        if ctx.protected_args:
            return super().invoke(ctx)

        # The following code is largely copied from the base implementation that can be found in
        # click.core.MultiCommand.

        def _process_result(value: t.Any) -> t.Any:
            if self._result_callback is not None:
                value = ctx.invoke(self._result_callback, value, **ctx.params)
            return value

        args = [*ctx.protected_args, *ctx.args]
        ctx.args = []
        ctx.protected_args = []

        with ctx:
            contexts = []
            for cmd_name in self.list_commands(ctx):
                if not ctx.params.get(cmd_name, True):
                    continue

                cmd = self.get_command(ctx, cmd_name)
                sub_ctx = cmd.make_context(
                    cmd_name,
                    args,
                    parent=ctx,
                    allow_extra_args=True,
                    allow_interspersed_args=False
                )
                contexts.append(sub_ctx)
                args, sub_ctx.args = sub_ctx.args, []

            rv = []
            for sub_ctx in contexts:
                with sub_ctx:
                    rv.append(sub_ctx.command.invoke(sub_ctx))
            return _process_result(rv)


@click.group(cls=WorkflowCommand, invoke_without_command=True)
@click.option(
    "--config", default=pathlib.Path('hermes.toml'),
    help="Configuration file in TOML format", type=pathlib.Path
)
@click.option("--curate", is_flag=True, default=False)
@click.option("--deposit", is_flag=True, default=False)
@click.option("--postprocess", is_flag=True, default=False)
@click.option("--clean", is_flag=True, default=False)
@click.option('--path', default=pathlib.Path('./'), help='Working path', type=pathlib.Path)
@click.pass_context
def main(ctx: click.Context, *args, **kwargs) -> None:
    """
    HERMES

    This command runs the HERMES workflow or parts of it.
    """

    pass


main.add_command(workflow.clean)
main.add_command(workflow.harvest)
main.add_command(workflow.process)
main.add_command(workflow.curate)
main.add_command(workflow.deposit)
main.add_command(workflow.postprocess)
