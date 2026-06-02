from importlib.metadata import metadata


def test_package_importable():
    import trainpit

    assert trainpit.__name__ == "trainpit"


def test_distribution_metadata_available():
    assert metadata("trainpit")["Name"] == "trainpit"
