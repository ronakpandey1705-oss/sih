import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.services.products.product_service import ProductService

# Use a separate SQLite database for testing
TEST_DB_URL = "sqlite:///./test_legal_metrology.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Setup tables in test DB
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    ProductService.seed_demo_products(db)
    from app.main import _seed_demo_officers
    _seed_demo_officers(db)
    db.close()

    yield

    # Teardown
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_legal_metrology.db"):
        try:
            os.remove("./test_legal_metrology.db")
        except Exception:
            pass


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
