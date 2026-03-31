"""
SharedStore — typed, persistent, cross-bot shared data collections.

Provides async CRUD operations on named collections backed by JSON files.
Each collection is a list of Pydantic model instances stored under
``shared/data/<collection_name>.json``.

Thread and async safety is guaranteed via ``asyncio.Lock`` — only one
coroutine can read or write a collection at a time.

Usage inside a task::

    from shared.models.todo import TodoItem

    items = await self.shared.load("todos", TodoItem)
    items.append(TodoItem(title="Buy milk"))
    await self.shared.save("todos", items)
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

COLLECTION_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
DATA_DIR = Path(__file__).parent / "data"


def _validate_collection_name(name: str) -> None:
    """Ensure the collection name is safe for use as a filename.

    Raises:
        ValueError: If the name is invalid.
    """
    if not COLLECTION_NAME_PATTERN.match(name):
        raise ValueError(
            f"Collection name must match {COLLECTION_NAME_PATTERN.pattern!r}, "
            f"got {name!r}."
        )


class SharedStore:
    """Async-safe, Pydantic-typed, JSON-backed shared data store.

    Parameters
    ----------
    data_dir:
        Directory where collection JSON files are stored.
        Defaults to ``shared/data/``.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or DATA_DIR
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, collection: str) -> asyncio.Lock:
        """Return a per-collection lock, creating it lazily."""
        if collection not in self._locks:
            self._locks[collection] = asyncio.Lock()
        return self._locks[collection]

    def _collection_path(self, collection: str) -> Path:
        """Return the JSON file path for a named collection."""
        return self._data_dir / f"{collection}.json"

    async def load(
        self,
        collection: str,
        model: type[T],
    ) -> list[T]:
        """Load all items from a named collection.

        Parameters
        ----------
        collection:
            Name of the collection (e.g. ``"todos"``).
        model:
            Pydantic model class to deserialize each item into.

        Returns
        -------
        list[T]:
            Validated model instances. Empty list if the collection
            does not exist yet.
        """
        _validate_collection_name(collection)
        lock = self._get_lock(collection)
        async with lock:
            return self._read(collection, model)

    async def save(
        self,
        collection: str,
        items: list[T],
    ) -> None:
        """Overwrite a collection with a new list of items.

        Parameters
        ----------
        collection:
            Name of the collection.
        items:
            Pydantic model instances to persist.
        """
        _validate_collection_name(collection)
        lock = self._get_lock(collection)
        async with lock:
            self._write(collection, items)

    async def append(
        self,
        collection: str,
        item: T,
        model: type[T],
    ) -> list[T]:
        """Append a single item to a collection and persist.

        Parameters
        ----------
        collection:
            Name of the collection.
        item:
            Pydantic model instance to append.
        model:
            Model class (needed to deserialize existing items on load).

        Returns
        -------
        list[T]:
            The updated collection after appending.
        """
        _validate_collection_name(collection)
        lock = self._get_lock(collection)
        async with lock:
            items = self._read(collection, model)
            items.append(item)
            self._write(collection, items)
            return list(items)

    async def remove(
        self,
        collection: str,
        index: int,
        model: type[T],
    ) -> T:
        """Remove an item by index and persist.

        Parameters
        ----------
        collection:
            Name of the collection.
        index:
            Zero-based index of the item to remove.
        model:
            Model class (needed to deserialize existing items on load).

        Returns
        -------
        T:
            The removed item.

        Raises
        ------
        IndexError:
            If the index is out of range.
        """
        _validate_collection_name(collection)
        lock = self._get_lock(collection)
        async with lock:
            items = self._read(collection, model)
            if not 0 <= index < len(items):
                raise IndexError(
                    f"Index {index} out of range for collection "
                    f"{collection!r} (size {len(items)})."
                )
            removed = items.pop(index)
            self._write(collection, items)
            return removed

    async def update(
        self,
        collection: str,
        index: int,
        item: T,
        model: type[T],
    ) -> list[T]:
        """Replace an item at a given index and persist.

        Parameters
        ----------
        collection:
            Name of the collection.
        index:
            Zero-based index of the item to replace.
        item:
            New Pydantic model instance.
        model:
            Model class (needed to deserialize existing items on load).

        Returns
        -------
        list[T]:
            The updated collection.

        Raises
        ------
        IndexError:
            If the index is out of range.
        """
        _validate_collection_name(collection)
        lock = self._get_lock(collection)
        async with lock:
            items = self._read(collection, model)
            if not 0 <= index < len(items):
                raise IndexError(
                    f"Index {index} out of range for collection "
                    f"{collection!r} (size {len(items)})."
                )
            items[index] = item
            self._write(collection, items)
            return list(items)

    async def clear(self, collection: str) -> None:
        """Remove all items from a collection.

        Parameters
        ----------
        collection:
            Name of the collection to clear.
        """
        _validate_collection_name(collection)
        lock = self._get_lock(collection)
        async with lock:
            self._write(collection, [])

    # ------------------------------------------------------------------
    # Internal I/O (synchronous — called under the async lock)
    # ------------------------------------------------------------------

    def _read(self, collection: str, model: type[T]) -> list[T]:
        """Deserialize a collection from disk."""
        path = self._collection_path(collection)
        if not path.exists():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            log.exception("Failed to read collection %r from %s", collection, path)
            return []
        return [model.model_validate(entry) for entry in raw]

    def _write(self, collection: str, items: list[BaseModel]) -> None:
        """Serialize a collection to disk."""
        path = self._collection_path(collection)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [item.model_dump(mode="json") for item in items]
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
