import pytest
from pathlib import Path
from examples.inventory_app.inventory import InventoryDB


def test_example_inventory_full_flow(tmp_path: Path):
    db_file = tmp_path / "inventory.db"
    inv = InventoryDB(db_file)

    # Add items
    item1 = inv.add_or_update_item("SKU-1", "Widget A", 100, 1500)
    item2 = inv.add_or_update_item("SKU-2", "Widget B", 3, 2500)

    assert item1.quantity == 100
    assert item2.quantity == 3

    # Low stock
    low = inv.list_low_stock(threshold=5)
    assert len(low) == 1
    assert low[0].sku == "SKU-2"

    # Delete
    assert inv.delete_item("SKU-1") is True
    assert inv.get_item_by_sku("SKU-1") is None
