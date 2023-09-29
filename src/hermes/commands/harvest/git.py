# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Jeffrey Kelling
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat

import logging
import os
import pathlib
import typing as t

import click
import subprocess
import shutil

from hermes.model.context import HermesHarvestContext
from hermes.model.errors import HermesValidationError


_log = logging.getLogger('harvest.git')


# TODO: can and should we get this somehow?
SHELL_ENCODING = 'utf-8'

_GIT_SEP = '|'
_GIT_FORMAT = ['%aN', '%aE', '%aI', '%cN', '%cE', '%cI']
_GIT_ARGS = ["--no-show-signature"]


# TODO The following code contains a lot of duplicate implementation that can be found in hermes.model
#      (In fact, it was kind of the prototype for lots of stuff there.)
#      Clean up and refactor to use hermes.model instead

class ContributorData:
    """
    Stores contributor data information from Git history.
    """

    def __init__(self, name: str | t.List[str], email: str | t.List[str], timestamp: str | t.List[str],
                 role: str | t.List[str]):
        """
        Initialize a new contributor dataset.

        :param name: Name as returned by the `git log` command (i.e., with `.mailmap` applied).
        :param email: Email address as returned by the `git log` command (also with `.mailmap` applied).
        :param timestamp: Timestamp when the respective commit was done.
        :param role: Role that the contributor fulfills for the respective commit.
        """
        self.name = []
        self.email = []
        self.timestamp = []
        self.role = []

        self.update(name=name, email=email, timestamp=timestamp, role=role)

    def __str__(self):
        parts = []
        if self.name:
            parts.append(self.name[0])
        if self.email:
            parts.append(f'<{self.email[0]}>')
        return f'"{" ".join(parts)}"'

    def _update_attr(self, target, value, unique=True):
        match value:
            case list():
                target.extend([v for v in value if not unique or v not in target])
            case str() if not unique or value not in target:
                target.append(value)

    def update(self, name=None, email=None, timestamp=None, role=None):
        """
        Update the current contributor with the given data.

        :param name: New name to assign (addtionally).
        :param email: New email to assign (additionally).
        :param timestamp: New timestamp to adapt time range.
        """
        self._update_attr(self.name, name)
        self._update_attr(self.email, email)
        self._update_attr(self.timestamp, timestamp, unique=False)
        self._update_attr(self.role, role)

    def merge(self, other: 'ContributorData'):
        """
        Merge another :py:class:`ContributorData` instance into this one.

        All attributes will be merged yet kept unique if required.

        :param other: The other instance that should contribute to this.
        """
        self.name += [n for n in other.name if n not in self.name]
        self.email += [e for e in other.email if e not in self.email]
        self.timestamp += other.timestamp
        self.role += [r for r in other.role if r not in self.role]

    def to_codemeta(self) -> dict:
        """
        Return the current dataset as CodeMeta.

        :return: The CodeMeta representation of this dataset.
        """
        # Person as type is fine even for bots, as they need to have emails,
        # and the Person type can be a fictional person in schema.org.
        res = {
            '@type': 'Person',
        }

        if self.name:
            res['name'] = self.name.pop()
        if self.name:
            res['alternateName'] = list(self.name)

        if self.email:
            res['email'] = self.email.pop(0)
        if self.email:
            res['contactPoint'] = [{'@type': 'ContactPoint', 'email': email} for email in self.email]

        if self.role:
            if self.timestamp:
                timestamp_start, *_, timestamp_end = sorted(self.timestamp + [self.timestamp[0]])
                res['hermes:contributionRole'] = [
                    {'@type': 'Role', 'roleName': role, 'startTime': timestamp_start, 'endTime': timestamp_end}
                    for role in self.role]
            else:
                res['hermes:contributionRole'] = [{'@type': 'Role', 'roleName': role} for role in self.role]

        return res


class NodeRegister:
    """
    Helper class to unify Git commit authors and committers.

    This class keeps track of all registered instances and merges two :py:class:`ContributorData` instances if some
    attributes match.
    """

    def __init__(self, cls, *order, **mapping):
        """
        Initalize a new register.

        :param cls: Type of objects to store.
        :param order: The order of attributes to compare.
        :param mapping: A mapping to convert attributes (will be applied for comparison).
        """
        self.cls = cls
        self.order = order
        self.mapping = mapping
        self._all = []
        self._node_by = {key: {} for key in self.order}

    def add(self, node: t.Any):
        """
        Add (or merge) a new node to the register.
        :param node: The node that should be added.
        """
        self._all.append(node)

        for key in self.order:
            mapping = self.mapping.get(key, lambda x: x)
            attr = getattr(node, key, None)
            match attr:
                case None:
                    continue
                case list():
                    for value in attr:
                        self._node_by[key][mapping(value)] = node

    def update(self, **kwargs):
        """
        Add (or merge) a new item to the register with the given attribute values.

        :fixme: This is not a good implementation strategy at all.

        :param kwargs: The attribute values to be stored.
        """
        missing = []
        tail = list(self.order)
        while tail:
            key, *tail = tail
            if key not in kwargs:
                continue

            arg = kwargs[key]
            node = self._node_by[key].get(arg, None)
            if node is None:
                missing.append((key, arg))
                continue

            node.update(**kwargs)
            break
        else:
            node = self.cls(**kwargs)
            self._all.append(node)

        for key in tail:
            if key not in kwargs:
                continue

            arg = kwargs[key]
            alt_node = self._node_by[key].get(arg, None)
            if alt_node is None:
                missing.append((key, arg))

            elif alt_node != node:
                node.merge(alt_node)
                self._all.remove(alt_node)
                self._node_by[key][arg] = node

        for key, arg in missing:
            self._node_by[key][arg] = node


def _audit_contributors(contributors, audit_log: logging.Logger):
    # Collect all authors that have ambiguous data
    unmapped_contributors = [a for a in contributors._all if len(a.email) > 1 or len(a.name) > 1]

    if unmapped_contributors:
        # Report to the audit about our findings
        audit_log.warning('!!! warning "You have unmapped contributors in your Git history."')
        for contributor in unmapped_contributors:
            if len(contributor.email) > 1:
                audit_log.info("    - %s has alternate email: %s", str(contributor), ', '.join(contributor.email[1:]))
            if len(contributor.name) > 1:
                audit_log.info("    - %s has alternate names: %s", str(contributor), ', '.join(contributor.name[1:]))
        audit_log.warning('')

        audit_log.info(
            "Please consider adding a `.maillog` file to your repository to disambiguate these contributors.")
        audit_log.info('')
        audit_log.info('``` .mailmap')

        audit_log.info('```')


def _merge_contributors(git_authors: NodeRegister, git_committers: NodeRegister) -> NodeRegister:
    """
    Merges the git authors and git committers :py:class:`NodeRegister` and assign the respective roles for each node.
    """
    git_contributors = NodeRegister(ContributorData, 'email', 'name', email=str.upper)
    for author in git_authors._all:
        git_contributors.update(email=author.email[0], name=author.name[0], timestamp=author.timestamp,
                                role='git author')

    for committer in git_committers._all:
        git_contributors.update(email=committer.email[0], name=committer.name[0], timestamp=committer.timestamp,
                                role='git committer')

    return git_contributors


def harvest_git(click_ctx: click.Context, ctx: HermesHarvestContext):
    """
    Implementation of a harvester that provides autor data from Git.

    :param click_ctx: Click context that this command was run inside (might be used to extract command line arguments).
    :param ctx: The harvesting context that should contain the provided metadata.
    """
    _log = logging.getLogger('cli.harvest.git')
    audit_log = logging.getLogger('audit.cff')
    audit_log.info('')
    audit_log.info("## Git History")

    # Get the parent context (every subcommand has its own context with the main click context as parent)
    parent_ctx = click_ctx.parent
    if parent_ctx is None:
        raise RuntimeError('No parent context!')

    _log.debug(". Get history of currently checked-out branch")

    git_authors = NodeRegister(ContributorData, 'email', 'name', email=str.upper)
    git_committers = NodeRegister(ContributorData, 'email', 'name', email=str.upper)

    git_exe = shutil.which('git')
    if not git_exe:
        raise RuntimeError('Git not available!')

    path = parent_ctx.params['path']
    old_path = pathlib.Path.cwd()
    if path != old_path:
        os.chdir(path)

    p = subprocess.run([git_exe, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)
    if p.returncode:
        raise HermesValidationError(f"`git branch` command failed with code {p.returncode}: "
                                    f"'{p.stderr.decode(SHELL_ENCODING).rstrip()}'!")

    git_branch = p.stdout.decode(SHELL_ENCODING).strip()
    # TODO: should we warn or error if the HEAD is detached?

    p = subprocess.run([git_exe, "log", f"--pretty={_GIT_SEP.join(_GIT_FORMAT)}"] + _GIT_ARGS, capture_output=True)
    if p.returncode:
        raise HermesValidationError(f"`git log` command failed with code {p.returncode}: "
                                    f"'{p.stderr.decode(SHELL_ENCODING).rstrip()}'!")

    log = p.stdout.decode(SHELL_ENCODING).split('\n')
    for line in log:
        try:
            # a = author, c = committer
            a_name, a_email, a_timestamp, c_name, c_email, c_timestamp = line.split(_GIT_SEP)
        except ValueError:
            continue

        git_authors.update(email=a_email, name=a_name, timestamp=a_timestamp, role=None)
        git_committers.update(email=c_email, name=c_name, timestamp=c_timestamp, role=None)

    git_contributors = _merge_contributors(git_authors, git_committers)

    _audit_contributors(git_contributors, logging.getLogger('audit.git'))

    ctx.update('contributor',
               [contributor.to_codemeta() for contributor in git_contributors._all],
               git_branch=git_branch)
    ctx.update('hermes:gitBranch', git_branch)

    try:
        ctx.get_data()
    except ValueError:
        audit_log.error('!!! warning "Inconsistent data"')
        audit_log.info('     The data collected from git is ambiguous.')
        audit_log.info('     Consider deleting `%s` to avoid problems.', ctx.hermes_dir)
        audit_log.error('')
