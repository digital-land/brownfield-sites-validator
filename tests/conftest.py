import pytest


@pytest.fixture(scope='session')
def upload():
    from tests.data.test_data import upload
    return upload


@pytest.fixture(scope='session')
def rows():
    from tests.data.test_data import rows
    return rows


@pytest.fixture(scope='session')
def meta_data():
    from tests.data.test_data import meta_data
    return meta_data
