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

    def invoke(self, ctx: click.Context) -> t.Any:
        """
        Invoke all sub-commands in a given order.

        If there is a flag in `ctx.params` with the name of a sub-command that evaluates to `False`,
        the command is not invoked.

        :param ctx: Context for the command.
        """

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
@click.option("--deposit", is_flag=True, default=False)
@click.option("--post", is_flag=True, default=False)
@click.option('--path', default='./', help='Working path', type=click.Path())
@click.pass_context
def haggis(ctx: click.Context, *args, **kwargs) -> None:
    """
    HERMES aggregated interface script

    This script can be used to run the HERMES pipeline or parts of it.
    """

    pass


haggis.add_command(workflow.harvest)
haggis.add_command(workflow.process)
haggis.add_command(workflow.deposit)
haggis.add_command(workflow.post)
