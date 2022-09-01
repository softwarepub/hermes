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

class AuthorData:
    def __init__(self, line: t.List):
        self.name = line[0]
        self.email = set((line[1],))
        self.tFirst = line[2]
        self.tLast = self.tFirst

    def update(self, line: t.List):
        assert(self.name == line[0])

        self.email.add(line[1])
        t = line[2]
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
    p = subprocess.run([gitExe, "log", "--pretty=%an_%ae_%ad", "--date=unix"], capture_output=True)
    if p.returncode:
        raise RuntimeError("`git log` command failed with code {}: '{}'!".format(p.returncode, p.stderr.decode(SHELL_ENCODING)))

    log = p.stdout.decode(SHELL_ENCODING).split('\n')
    for l in log:
        d = l.split('_')
        if len(d) != 3:
            continue
        try:
            d[2] = int(d[2])
        except ValueError:
            continue

        if d[0] in authors:
            authors[d[0]].update(d)
        else:
            authors[d[0]] = AuthorData(d)
    
    for a in authors.values():
        ctx.update("author.since", a.tFirst, name=a.name, branch=gitBranch)
        ctx.update("author.until", a.tLast, name=a.name, branch=gitBranch)
        for e in a.email:
            ctx.update("author.email", e, name=a.name, branch=gitBranch, email=e)
