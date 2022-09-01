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
        self.tFirst = d[2]
        self.tLast = self.tFirst

    def update(self, d: t.List):
        assert(self.name == d[0])

        self.email.add(d[1])
        t = d[2]
        if t < self.tFirst:
            self.tFirst = t
        elif t > self.tFirst:
            self.tLast = t

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

    gitExe = shutil.which('git')
    if not gitExe:
        raise RuntimeError('Git not available!')

    p = subprocess.run([gitExe, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)
    if p.returncode:
        raise RuntimeError("`git branch` command failed with code {}: '{}'!".format(p.returncode, p.stderr.decode(SHELL_ENCODING)))
    gitBranch = p.stdout.decode(SHELL_ENCODING).strip()
    # TODO: should we warn or error if the HEAD is detached?

    # Get history of currently checked-out branch
    authors = {}
    committers = {}
    p = subprocess.run([gitExe, "log", "--pretty=%an_%ae_%at_%cn_%ce_%ct"], capture_output=True)
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
    
    _ctxUpdateContributors(ctx, authors, "author", branch=gitBranch)
    _ctxUpdateContributors(ctx, committers, "committer", branch=gitBranch)

def _updateContributor(contributors: t.Dict, d: t.List):
    if d[0] in contributors:
        contributors[d[0]].update(d[0:3])
    else:
        contributors[d[0]] = ConributorData(d[0:3])

def _ctxUpdateContributors(ctx: HermesHarvestContext, contributors: t.Dict, kind: str, **kwargs):
    for a in contributors.values():
        ctx.update(f"{kind}.since", a.tFirst, name=a.name, **kwargs)
        ctx.update(f"{kind}.until", a.tLast, name=a.name, **kwargs)
        for e in a.email:
            ctx.update(f"{kind}.email", e, name=a.name, email=e, **kwargs)
