import pytest
from pathlib import Path
from examples.inventory_app.inventory import InventoryDB


def test_inventory_add_and_get(tmp_path: Path):
    db_file = tmp_path / "test_inventory.db"
    store = InventoryDB(db_file)

    item = store.add_or_update_item(
        sku="SKU-1001",
        name="Wireless Keyboard",
        quantity=15,
        price_cents=2999,
    )

    assert item.id is not None
    assert item.sku == "SKU-1001"
    assert item.name == "Wireless Keyboard"
    assert item.quantity == 15
    assert item.price_cents == 2999

    fetched = store.get_item_by_sku("SKU-1001")
    assert fetched is not None
    assert fetched.name == "Wireless Keyboard"


def test_inventory_upsert_quantity(tmp_path: Path):
    db_file = tmp_path / "test_inventory.db"
    store = InventoryDB(db_file)

    store.add_or_update_item(sku="SKU-1002", name="USB Cable", quantity=10, price_cents=500)
    # Upsert with new quantity
    updated = store.add_or_update_item(sku="SKU-1002", name="USB Cable v2", quantity=25, price_cents=600)

    assert updated.quantity == 25
    assert updated.name == "USB Cable v2"
    assert updated.price_cents == 600


def test_inventory_low_stock_filter(tmp_path: Path):
    db_file = tmp_path / "test_inventory.db"
    store = InventoryDB(db_file)

    store.add_or_update_item(sku="ITEM-HIGH", name="High Stock Widget", quantity=50, price_cents=100)
    store.add_or_update_item(sku="ITEM-LOW1", name="Low Stock Bolt", quantity=2, price_cents=10)
    store.add_or_update_item(sku="ITEM-LOW2", name="Low Stock Nut", quantity=0, price_cents=5)

    low_items = store.list_low_stock(threshold=5)
    assert len(low_items) == 2
    skus = [i.sku for i in low_items]
    assert "ITEM-LOW1" in skus
    assert "ITEM-LOW2" in skus
    assert "ITEM-HIGH" not in skus


def test_inventory_delete(tmp_path: Path):
    db_file = tmp_path / "test_inventory.db"
    store = InventoryDB(db_file)

    store.add_or_update_item(sku="ITEM-DEL", name="Delete Me", quantity=1, price_cents=10)
    assert store.get_item_by_sku("ITEM-DEL") is not None

    deleted = store.delete_item("ITEM-DEL")
    assert deleted is True
    assert store.get_item_by_sku("ITEM-DEL") is None
