import pytest


@pytest.fixture(scope='session')
def original_data():
    from tests.data.test_data import original_data
    return original_data


@pytest.fixture(scope='session')
def validated_data():
    from tests.data.test_data import validated_data
    return validated_data


@pytest.fixture(scope='session')
def additional_data():
    from tests.data.test_data import additional_data
    return additional_data
