import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from validator.standards import BrownfieldStandard
from validator.validation_result import Result

from application.factory import create_app
from application.extensions import db as _db


@pytest.fixture(scope="session")
def app(request):
    app = create_app("config.TestConfig")

    ctx = app.test_request_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def db(app, request):
    def teardown():
        _db.drop_all()

    _db.app = app
    _db.create_all()

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope="session")
def session(db):
    engine = create_engine(db.engine.url)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="session")
def standard():
    return BrownfieldStandard()


@pytest.fixture(scope="session")
def result(standard):
    from tests.data.result import result as _result

    return Result.factory(_result, standard)


@pytest.fixture(scope="session")
def csv_file():
    path = os.path.dirname(os.path.realpath(__file__))
    csv_file_path = os.path.join(path, "data", "test-brownfield-register.csv")
    return csv_file_path
