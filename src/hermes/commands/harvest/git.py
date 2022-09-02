import glob
import os
import json
import pathlib
import urllib.request
import typing as t

import jsonschema
import click
import subprocess
import shutil

from hermes.model.context import HermesHarvestContext
from hermes.model.errors import HermesValidationError

# TODO: can and should we get this somehow?
SHELL_ENCODING = 'utf-8'


class ConributorData:
    def __init__(self, d: t.List):
        self.name = d[0]
        self.email = set((d[1],))
        self.t_first= d[2]
        self.t_last= self.t_first

    def update(self, d: t.List):
        assert(self.name == d[0])

        self.email.add(d[1])
        t = d[2]
        if t < self.t_first:
            self.t_first = t
        elif t > self.t_first:
            self.t_last = t


def harvest_git(click_ctx: click.Context, ctx: HermesHarvestContext):
    """
    Implementation of a harvester that provides autor data from Git.

    :param click_ctx: Click context that this command was run inside (might be used to extract command line arguments).
    :param ctx: The harvesting context that should contain the provided metadata.
    """
    # Get the parent context (every subcommand has its own context with the main click context as parent)
    parent_ctx = click_ctx.parent
    if parent_ctx is None:
        raise RuntimeError('No parent context!')
    path = parent_ctx.params['path']

    git_exe = shutil.which('git')
    if not git_exe:
        raise RuntimeError('Git not available!')

    p = subprocess.run([git_exe, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)
    if p.returncode:
        raise RuntimeError("`git branch` command failed with code {}: '{}'!".format(p.returncode, p.stderr.decode(SHELL_ENCODING)))
    git_branch = p.stdout.decode(SHELL_ENCODING).strip()
    # TODO: should we warn or error if the HEAD is detached?

    # Get history of currently checked-out branch
    authors = {}
    committers = {}
    p = subprocess.run([git_exe, "log", "--pretty=%an_%ae_%at_%cn_%ce_%ct"], capture_output=True)
    if p.returncode:
        raise RuntimeError("`git log` command failed with code {}: '{}'!".format(p.returncode, p.stderr.decode(SHELL_ENCODING)))

    log = p.stdout.decode(SHELL_ENCODING).split('\n')
    for l in log:
        d = l.split('_')
        if len(d) != 6:
            continue
        try:
            d[2] = int(d[2])
        except ValueError:
            continue

        _updateContributor(authors, d[0:3])
        _updateContributor(committers, d[3:7])
    
    _ctx_update_contributors(ctx, authors, "author", branch=git_branch)
    _ctx_update_contributors(ctx, committers, "committer", branch=git_branch)

def _update_contributor(contributors: t.Dict, d: t.List):
    if d[0] in contributors:
        contributors[d[0]].update(d[0:3])
    else:
        contributors[d[0]] = ConributorData(d[0:3])


def _ctx_update_contributors(ctx: HermesHarvestContext, contributors: t.Dict, kind: str, **kwargs):
    for a in contributors.values():
        ctx.update(f"{kind}.since", a.t_first, name=a.name, **kwargs)
        ctx.update(f"{kind}.until", a.t_last, name=a.name, **kwargs)
        for e in a.email:
            ctx.update(f"{kind}.email", e, name=a.name, email=e, **kwargs)
