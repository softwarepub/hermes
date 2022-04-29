"""
This module provides the main entry point for the HERMES command line application.
"""
import typing as t

import click

from hermes.commands import workflow


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

    def invoke_all(self, ctx: click.Context) -> None:
        """
        Invoke all sub-commands in a given order.

        If there is a flag in `ctx.params` with the name of a sub-command that evaluates to `False`,
        the command is not invoked.

        :param ctx: Context for the command.
        """

        for sub in self.list_commands(ctx):
            if ctx.params.get(sub, True):
                ctx.invoke(self.get_command(ctx, sub))


@click.group(cls=WorkflowCommand, invoke_without_command=True)
@click.option("--deposit", is_flag=True, default=False)
@click.option("--post", is_flag=True, default=False)
@click.pass_context
def haggis(ctx: click.Context, *args, **kwargs) -> None:
    """
    HERMES aggregated interface script

    This script can be used to run the HERMES pipeline or parts of it.
    """
    if ctx.invoked_subcommand is None:
        ctx.command.invoke_all(ctx)


haggis.add_command(workflow.harvest)
haggis.add_command(workflow.process)
haggis.add_command(workflow.deposit)
haggis.add_command(workflow.post)
