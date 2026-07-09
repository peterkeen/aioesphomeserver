def test_package_imports():
    import aioesphomeserver

    assert aioesphomeserver.Device is not None
    assert aioesphomeserver.NativeApiServer is not None
