import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import pytest
from shared.store import SharedStore
from pydantic import BaseModel


class TestItem(BaseModel):
    title: str


@pytest.fixture
def shared_store(tmp_path):
    """Provide a SharedStore instance with a temporary data directory."""
    store = SharedStore(data_dir=tmp_path)
    yield store


@pytest.mark.asyncio
async def test_load_empty_collection(shared_store):
    """Test loading a non-existent collection returns an empty list."""
    items = await shared_store.load("test", TestItem)
    assert items == []


@pytest.mark.asyncio
async def test_save_and_load_collection(shared_store):
    """Test saving and loading a collection."""
    items = [TestItem(title="Item 1"), TestItem(title="Item 2")]
    await shared_store.save("test", items)

    loaded_items = await shared_store.load("test", TestItem)
    assert len(loaded_items) == 2
    assert loaded_items[0].title == "Item 1"
    assert loaded_items[1].title == "Item 2"


@pytest.mark.asyncio
async def test_append_to_collection(shared_store):
    """Test appending an item to a collection."""
    await shared_store.append("test", TestItem(title="Item 1"), TestItem)
    await shared_store.append("test", TestItem(title="Item 2"), TestItem)

    items = await shared_store.load("test", TestItem)
    assert len(items) == 2
    assert items[0].title == "Item 1"
    assert items[1].title == "Item 2"


@pytest.mark.asyncio
async def test_remove_from_collection(shared_store):
    """Test removing an item by index."""
    items = [TestItem(title="Item 1"), TestItem(title="Item 2")]
    await shared_store.save("test", items)

    removed = await shared_store.remove("test", 0, TestItem)
    assert removed.title == "Item 1"

    remaining_items = await shared_store.load("test", TestItem)
    assert len(remaining_items) == 1
    assert remaining_items[0].title == "Item 2"


@pytest.mark.asyncio
async def test_update_collection(shared_store):
    """Test updating an item by index."""
    items = [TestItem(title="Item 1"), TestItem(title="Item 2")]
    await shared_store.save("test", items)

    updated_items = await shared_store.update("test", 1, TestItem(title="Updated Item 2"), TestItem)
    assert updated_items[1].title == "Updated Item 2"


@pytest.mark.asyncio
async def test_clear_collection(shared_store):
    """Test clearing a collection."""
    items = [TestItem(title="Item 1"), TestItem(title="Item 2")]
    await shared_store.save("test", items)

    await shared_store.clear("test")
    cleared_items = await shared_store.load("test", TestItem)
    assert cleared_items == []