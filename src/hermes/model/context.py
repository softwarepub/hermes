import traceback
import json
import logging
import typing as t

from pathlib import Path
from importlib.metadata import EntryPoint

from hermes.model.errors import HermesValidationError


_log = logging.getLogger(__name__)


class HermesContext:
    """
    The HermesContext stores the metadata for a certain project.

    As there are different views of the metadata in the different stages,
    some stages use a special subclass of this context:

    - The *harvest* stages uses :class:`HermesHarvestContext`.
    """

    def __init__(self, project_dir: t.Optional[Path] = None):
        """
        Create a new context for the given project dir.

        :param project_dir: The root directory of the project.
                            If nothing is given, the current working directory is used.
        """

        #: Base dir for the hermes metadata cache (default is `.hermes` in the project root).
        self.hermes_dir = Path(project_dir or '.') / '.hermes'

        self._caches = {}
        self._data = {}
        self._errors = []

    def get_cache(self, *path: str, create: bool = False) -> Path:
        """
        Retrieve a cache file for a given *path*.

        This method returns an appropriate path to a file but does not make any assertions about the format, encoding,
        or whether the file should be exists.
        However, it is capable to create the enclosing directory (if you specify `create = True`).

        :param path: The (local) path to identify the requested cache.
        :param create: Select whether the directory should be created.
        :return: The path to the requested cache file.
        """

        if path in self._caches:
            return self._caches[path]

        *subdir, name = path
        cache_dir = self.hermes_dir.joinpath(*subdir)
        if create:
            cache_dir.mkdir(parents=True, exist_ok=True)
        data_file = cache_dir / name
        self._caches[path] = data_file

        return data_file

    def update(self, _key: str, _value: t.Any, **kwargs: t.Any):
        """
        Store a new value for a given key to the context.

        :param _key: The key may be a dotted name for a metadata attribute to store.
        :param _value: The value that should be stored for the key.
        :param kwargs: Additional information about the value.
                       This can be used to trace back the original value.
                       If `_ep` is given, it is treated as an entry point name that triggered the update.
        """

        pass

    def error(self, ep: EntryPoint, error: Exception):
        """
        Add an error that occurred during processing to the error log.

        :param ep: The entry point that produced the error.
        :param error: The exception that was thrown due to the error.
        """

        self._errors.append((ep, error))


class HermesHarvestContext(HermesContext):
    """
    A specialized context for use in *harvest* stage.

    Each harvester has its own context that is cached to :py:attr:`HermesContext.hermes_dir` `/harvest/EP_NAME`.

    This special context is implemented as a context manager that loads the cached data upon entering the context.
    When the context is left, recorded metadata is stored in a cache file possible errors are propagated to the
    parent context.
    """

    def __init__(self, base: HermesContext, ep: EntryPoint):
        """
        Initialize a new harvesting context.

        :param base: The base HermesContext that should receive the results of the harvesting.
        :param ep: The entry point that implements the harvester using this context.
        """

        super().__init__()

        self._base = base
        self._ep = ep
        self._log = logging.getLogger(f'harvest.{self._ep.name}')

    def load_cache(self):
        """
        Load the cached data from the :py:attr:`HermesContext.hermes_dir`.
        """

        data_file = self._base.get_cache('harvest', self._ep.name)
        if data_file.is_file():
            self._log.debug("Loading cache from %s...", data_file)
            self._data = json.load(data_file.open('r'))

    def store_cache(self):
        """
        Store the collected data to the :py:attr:`HermesContext.hermes_dir`.
        """

        data_file = self.get_cache('harvest', self._ep.name, create=True)
        self._log.debug("Writing cache to %s...", data_file)
        json.dump(self._data, data_file.open('w'))

    def __enter__(self):
        self.load_cache()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.store_cache()
        if exc_type is not None and issubclass(exc_type, HermesValidationError):
            exc = traceback.TracebackException(exc_type, exc_val, exc_tb)
            self._base.error(self._ep, exc)
            return True

    def update(self, _key: str, _value: t.Any, **kwargs: t.Any):
        """
        The updates are added to a list of values.
        A value is only replaced if the `_key` and all `kwargs` match.

        .. code:: python

            # 'value 2' will be added (twice)
            ctx.update('key', 'value 1', spam='eggs')
            ctx.update('key', 'value 2', foo='bar')
            ctx.update('key', 'value 2', foo='bar', spam='eggs')

            # 'value 2' will replace 'value 1'
            ctx.update('key', 'value 1', spam='eggs')
            ctx.update('key', 'value 2', spam='eggs')

        This way, the harvester can fully specify the source and only override values that are from the same origin
        (e.g., if the data changed between two runs).

        See :py:meth:`HermesContext.update` for more information.
        """

        if _key not in self._data:
            self._data[_key] = []

        for entry in self._data[_key]:
            if entry[1] == kwargs:
                self._log.debug("Update %s: %s -> %s (%s)", _key, entry[0], _value, entry[1])
                entry[0] = _value
                break
        else:
            self._data[_key].append([_value, kwargs])

    def _update_key_from(self, _key: str, _value: t.Any, **kwargs):
        if isinstance(_value, dict):
            for key, value in _value.items():
                self._update_key_from(f'{_key}.{key}', _value, **kwargs)
            else:
                self.update(_key, _value, **kwargs)

    def update_from(self, data: t.Dict[str, t.Any], **kwargs: t.Any):
        """
        Bulk-update multiple values.

        If the value for a certain key is again a dictionary, the key will be expanded. I.e.

        .. code:: python

            ctx.update_from({'foo': 'bar', 'author': {'name': 'Monty Python', 'email': 'eggs@spam.xxx'}})

        will evetually result in the following calls:

        .. code:: python

            ctx.update('foo', 'bar')
            ctx.update('author.name', 'Monty Python')
            ctx.update('author.email', 'eggs@spam.xxx')

        :param data: The data that should be updated (as mapping with strings as keys).
        :param kwargs: Additional information about the value (see :ref:`HermesContext.update` for details).
        """

        for key, value in data.items():
            self._update_key_from(key, value, **kwargs)

    def error(self, ep: EntryPoint, error: Exception):
        """
        See :py:meth:`HermesContext.error`
        """

        ep = ep or self._ep
        self._base.error(ep, error)
