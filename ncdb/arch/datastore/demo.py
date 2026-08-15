from pathlib import Path

from domain import DataProduct, DataStore
from devices import DatabaseDevice, FileSystemDevice


def main() -> None:
    # Start with a clean prototype.
    for filename in [
        "demo_datastore.db",
        "demo_device.db",
    ]:
        path = Path(filename)
        if path.exists():
            path.unlink()

    root = Path("demo_files")

    if root.exists():
        for path in root.rglob("*"):
            if path.is_file():
                path.unlink()

    root.mkdir(exist_ok=True)

    store = DataStore("demo_datastore.db")

    filesystem = FileSystemDevice(root)
    database = DatabaseDevice("demo_device.db")

    store.register_device(
        "filesystem",
        filesystem,
    )

    store.register_device(
        "database",
        database,
    )

    # ------------------------------------------------------------
    # A DataProduct is an existing Workflow asset.
    # ------------------------------------------------------------

    product = DataProduct(asset_id=1001)

    data = b"Hello from DataProduct 1001\n"

    # Put representations on two different devices.
    # filesystem.put(
        # "product-1001.dat",
        # data,
    # )
# 
    # database.put(
        # "1001",
        # data,
    # )

    # Tell the DataStore where the DataProduct is stored.
    store.register(
        product,
        device="filesystem",
        address="product-1001.dat",
        data=data
    )

    store.register(
        product,
        device="database",
        address="1001",
        data=data
    )

    print()
    print("=== PRODUCTS ===")
    print(store.list_products())

    print()
    print("=== LOCATIONS ===")
    for location in store.locations(1001):
        print(location)

    print()
    print("=== AVAILABILITY ===")
    for item in store.availability(1001):
        print(item)

    print()
    print("=== METADATA ===")
    for item in store.metadata(1001):
        print(item)

    print()
    print("=== GET ===")
    result = store.get(1001)
    print(result)

    print()
    print("=== DELETE ===")
    store.delete(1001)

    print("Products after delete:")
    print(store.list_products())


if __name__ == "__main__":
    main()
