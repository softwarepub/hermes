import datetime
import logging
import os
import pathlib
import typing as t

import click
import subprocess
import shutil

from hermes.model.context import HermesHarvestContext, ContextPath


_log = logging.getLogger('harvest.git')


# TODO: can and should we get this somehow?
SHELL_ENCODING = 'utf-8'

_GIT_SEP = '|'
_GIT_FORMAT = ['%aN', '%aE', '%aI']
_GIT_ARGS = []


# TODO The following code contains a lot of duplicate implementation that can be found in hermes.model
#      (In fact, it was kind of the prototype for lots of stuff there.)
#      Clean up and refactor to use hermes.model instead

class ContributorData:
    """
    Stores contributor data information from Git history.
    """

    def __init__(self, name: str | t.List[str], email: str | t.List[str], ts: str | t.List[str]):
        """
        Initialize a new contributor dataset.

        :param name: Name as returned by the `git log` command (i.e., with `.mailmap` applied).
        :param email: Email address as returned by the `git log` command (also with `.mailmap` applied).
        :param ts: Timestamp when the respective commit was done.
        """
        self.name = []
        self.email = []
        self.ts = []

        self.update(name=name, email=email, ts=ts)

    def __str__(self):
        parts = []
        if self.name: parts.append(self.name[0])
        if self.email: parts.append(f'<{self.email[0]}>')
        return f'"{" ".join(parts)}"'

    def _update_attr(self, target, value, unique=True):
        match value:
            case list():
                target.extend([v for v in value if not unique or v not in target])
            case str() if not unique or value not in target:
                target.append(value)

    def update(self, name=None, email=None, ts=None):
        """
        Update the current contributor with the given data.

        :param name: New name to assign (addtionally).
        :param email: New email to assign (additionally).
        :param ts: New timestamp to adapt time range.
        """
        self._update_attr(self.name, name)
        self._update_attr(self.email, email)
        self._update_attr(self.ts, ts, unique=False)

    def merge(self, other: 'ContributorData'):
        """
        Merge another :ref:`ContributorData` instance into this one.

        All attributes will be merged yet kept unique if required.

        :param other: The other instance that should contribute to this.
        """
        self.name += [n for n in other.name if n not in self.name]
        self.email += [e for e in other.email if e not in self.email]
        self.ts += other.ts

    def to_codemeta(self) -> dict:
        """
        Return the current dataset as CodeMeta.

        :return: The CodeMeta representation of this dataset.
        """
        res = {
            '@type': ['Person', 'hermes:contributor'],
        }

        if self.name:
            res['name'] = self.name.pop()
        if self.name:
            res['alternateName'] = list(self.name)

        if self.email:
            res['email'] = self.email.pop(0)
        if self.email:
            res['contactPoint'] = [{'@type': 'ContactPoint', 'email': email} for email in self.email]

        if self.ts:
            ts_start, *_, ts_end = sorted(self.ts + [self.ts[0]])
            res['startTime'] = ts_start
            res['endTime'] = ts_end

        return res

    @classmethod
    def from_codemeta(cls, data) -> 'ContributorData':
        """
        Initialize a new instance from CodeMeta representation.

        :param data: The CodeMeta dataset to initialize from.
        :return: The newly created instance.
        """
        name = [data['name']] + data.get('alternateName', [])
        email = [data['email']] + [contact['email'] for contact in data.get('contactPoint', [])]
        ts = [data['startTime'], data['endTime']]
        return cls(name, email, ts)


class NodeRegister:
    """
    Helper class to unify Git commit authors / contributors.

    This class keeps track of all registered instances and merges two :ref:`ContributorData` instances if some
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


def _audit_authors(authors, audit_log: logging.Logger):
    # Collect all authors that have ambiguous data
    unmapped_authors = []
    for author in authors._all:
        if len(author.email) > 1 or len(author.name) > 1:
            unmapped_authors.append(author)

    if unmapped_authors:
        # Report to the audit about our findings
        audit_log.warning('!!! warning "You have unmapped authors in your Git history."')
        for author in unmapped_authors:
            if len(author.email) > 1:
                audit_log.info(f"    - %s has alternate email: %s", str(author), ', '.join(author.email[1:]))
            if len(author.name) > 1:
                audit_log.info(f"    - %s has alternate names: %s", str(author), ', '.join(author.name[1:]))
        audit_log.warning('')

        audit_log.info("Please consider adding a `.maillog` file to your repository to disambiguate these contributors.")
        audit_log.info('')
        audit_log.info('``` .mailmap')

        # Provide some example configuration for the hint log
        hint_log = audit_log.parent.getChild('hints')
        hint_log.debug("# '.maillog' to resolve git ambiguities.")

        unmapped_email = [a for a in unmapped_authors if a.email[1:]]
        if unmapped_email:
            hint_log.debug('# Mapping of email addresses only. Format (one pair per line):')
            hint_log.debug('# <old.email@ddress> <new.email@address>')

            for author in unmapped_email:
                for email in author.email[1:]:
                    hint_log.info("<%s> <%s>", str(author.email[0]), str(email))
            hint_log.debug('')

        unmapped_name = [a for a in unmapped_authors if a.name[1:]]
        if unmapped_name:
            hint_log.debug('# Mapping of user names. Format (one pair per line):')
            hint_log.debug('# Real Name <email@ddress> nickname')
            hint_log.debug('# Real Name <email@ddress> Name, Real')

            for author in [a for a in unmapped_authors if a.name[1:]]:
                for name in author.name[1:]:
                    hint_log.info('%s <%s> %s', str(author.name[0]), str(author.email[0]), str(name))

        hint_log.info('')

        audit_log.info('```')


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

    authors = NodeRegister(ContributorData, 'email', 'name', email=str.upper)
    try:
        for author_data in ctx.get_data().get('author', []):
            authors.add(ContributorData.from_codemeta(author_data))
    except ValueError:
        pass

    git_exe = shutil.which('git')
    if not git_exe:
        raise RuntimeError('Git not available!')

    path = parent_ctx.params['path']
    old_path = pathlib.Path.cwd()
    if path != old_path:
        os.chdir(path)

    p = subprocess.run([git_exe, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)
    if p.returncode:
        raise RuntimeError("`git branch` command failed with code {}: '{}'!".format(p.returncode, p.stderr.decode(SHELL_ENCODING)))
    git_branch = p.stdout.decode(SHELL_ENCODING).strip()
    # TODO: should we warn or error if the HEAD is detached?

    p = subprocess.run([git_exe, "log", f"--pretty={_GIT_SEP.join(_GIT_FORMAT)}"] + _GIT_ARGS, capture_output=True)
    if p.returncode:
        raise RuntimeError("`git log` command failed with code {}: '{}'!".format(p.returncode, p.stderr.decode(SHELL_ENCODING)))

    log = p.stdout.decode(SHELL_ENCODING).split('\n')
    for l in log:
        try:
            name, email, ts = l.split(_GIT_SEP)
        except ValueError:
            continue

        authors.update(email=email, name=name, ts=ts)

    _audit_authors(authors, logging.getLogger('audit.git'))

    ctx.update_from({
        '@context': [
            "https://doi.org/10.5063/schema/codemeta-2.0",
            {'hermes': 'https://software-metadata.pub/ns/hermes/'}
        ],

        '@type': "SoftwareSourceCode",
        'author': [author.to_codemeta() for author in authors._all],
    }, branch=git_branch)

    try:
        ctx.get_data()
    except ValueError as e:
        audit_log.error('!!! warning "Inconsistent data"')
        audit_log.info('     The data collected from git is ambiguous.')
        audit_log.info('     Consider deleting `%s` to avoid problems.', ctx.hermes_dir)
        audit_log.error('')
