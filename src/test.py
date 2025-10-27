import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from src.db import Base, get_session
from src.main import app

# Setup test database
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def override_get_session():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """Setup and teardown database for each test"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(setup_database):
    """Async HTTP client for testing"""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_analyze_string(client: AsyncClient):
    response = await client.post("/strings", json={"value": "hello"})
    assert response.status_code == 201
    data = response.json()
    assert data["value"] == "hello"
    assert data["properties"]["length"] == 5
    assert not data["properties"]["is_palindrome"]
    assert data["properties"]["unique_characters"] == 4
    assert data["properties"]["word_count"] == 1
    assert "sha256_hash" in data["properties"]
    assert "character_frequency_map" in data["properties"]

@pytest.mark.asyncio
async def test_create_existing_string(client: AsyncClient):
    await client.post("/strings", json={"value": "test"})
    response = await client.post("/strings", json={"value": "test"})
    assert response.status_code == 409
    response_data = response.json()
    # Your API uses "message" or "detail"
    error_text = response_data.get("detail") or response_data.get("message") or str(response_data)
    assert "already exists" in error_text.lower()

@pytest.mark.asyncio
async def test_get_string_found(client: AsyncClient):
    await client.post("/strings", json={"value": "world"})
    response = await client.get("/strings/world")
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == "world"

@pytest.mark.asyncio
async def test_get_string_not_found(client: AsyncClient):
    response = await client.get("/strings/nonexistent")
    assert response.status_code == 404
    response_data = response.json()
    assert "not found" in (response_data.get("detail") or response_data.get("value") or str(response_data))

@pytest.mark.asyncio
async def test_create_string_missing_value(client: AsyncClient):
    response = await client.post("/strings", json={})
    assert response.status_code == 400
    response_data = response.json()
    print(f"\nDEBUG: Missing value response_data: {response_data}") # DEBUG
    # Adjusting assertion to be more flexible or specific to the actual 400 response
    detail_content = response_data.get("detail", "")
    errors_content = response_data.get("errors", [])
    assert "value is required" in str(detail_content).lower() or any("field required" in error.get("msg", "").lower() for error in errors_content)

@pytest.mark.asyncio
async def test_create_string_invalid_data_type(client: AsyncClient):
    response = await client.post("/strings", json={"value": 123})
    assert response.status_code == 400
    response_data = response.json()
    print(f"\nDEBUG: Invalid data type response_data: {response_data}") # DEBUG
    # Adjusting assertion to be more flexible or specific to the actual 400 response
    detail_content = response_data.get("detail", "")
    errors_content = response_data.get("errors", [])
    assert "input should be a valid string" in str(detail_content).lower() or any("input should be a valid string" in error.get("msg", "").lower() for error in errors_content)

@pytest.mark.asyncio
async def test_get_string_with_filters(client: AsyncClient):
    await client.post("/strings", json={"value": "madam"})
    await client.post("/strings", json={"value": "level"}) # Add another palindrome
    await client.post("/strings", json={"value": "hello"}) # Add a non-palindrome

    # Test with multiple filters
    response = await client.get("/strings?is_palindrome=true&min_length=5&max_length=5&word_count=1&contains_character=m")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["value"] == "madam"
    assert data["filters_applied"]["is_palindrome"] == True
    assert data["filters_applied"]["min_length"] == 5
    assert data["filters_applied"]["max_length"] == 5
    assert data["filters_applied"]["word_count"] == 1
    assert data["filters_applied"]["contains_character"] == "m"

    # Test with a filter that should yield no results
    response = await client.get("/strings?is_palindrome=false&contains_character=m")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0 # "madam" is a palindrome, "hello" does not contain 'm'

@pytest.mark.asyncio
async def test_query_strings_no_filters(client: AsyncClient):
    await client.post("/strings", json={"value": "apple"})
    await client.post("/strings", json={"value": "banana"})
    response = await client.get("/strings")
    
    # Debug: print response if not 200
    if response.status_code != 200:
        print(f"\n=== DEBUG query_strings_no_filters ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        try:
            print(f"JSON: {response.json()}")
        except:
            pass
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["count"] >= 2
    assert any(item["value"] == "apple" for item in data["data"])
    assert any(item["value"] == "banana" for item in data["data"])

@pytest.mark.asyncio
async def test_query_strings_with_filters(client: AsyncClient):
    await client.post("/strings", json={"value": "level"})
    await client.post("/strings", json={"value": "python"})
    response = await client.get("/strings?is_palindrome=true&min_length=5&max_length=5")
    
    # Debug: print response if not 200
    if response.status_code != 200:
        print(f"\n=== DEBUG query_strings_with_filters ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        try:
            print(f"JSON: {response.json()}")
        except:
            pass
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["value"] == "level"
    assert data["filters_applied"]["is_palindrome"] == True

@pytest.mark.asyncio
async def test_natural_language_filter(client: AsyncClient):
    # Use very distinct strings to avoid accidental matches from other tests
    await client.post("/strings", json={"value": "nl_apple_pie"})
    await client.post("/strings", json={"value": "nl_banana_split"})
    await client.post("/strings", json={"value": "nl_red_apple"})
    await client.post("/strings", json={"value": "nl_pineapple"})

    response = await client.get("/strings/filter-by-natural-language?query=strings containing 'apple'") # Added single quotes
    assert response.status_code == 200
    data = response.json()
    
    # Debug: print response if not 200 or count is unexpected
    if response.status_code != 200 or data["count"] != 3: # Expecting 3 now: nl_apple_pie, nl_red_apple, nl_pineapple
        print(f"\n=== DEBUG natural_language_filter (containing 'apple') ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        try:
            print(f"JSON: {response.json()}")
        except:
            pass

    assert data["count"] == 3 # nl_apple_pie, nl_red_apple, nl_pineapple
    assert any(item["value"] == "nl_apple_pie" for item in data["data"])
    assert any(item["value"] == "nl_red_apple" for item in data["data"])
    assert any(item["value"] == "nl_pineapple" for item in data["data"])

    # Test for palindromes
    await client.post("/strings", json={"value": "nl_madam"})
    await client.post("/strings", json={"value": "nl_level"})
    await client.post("/strings", json={"value": "nl_not_palindrome"})

    response = await client.get("/strings/filter-by-natural-language?query=palindromes")
    assert response.status_code == 200
    data = response.json()
    print(f"\nDEBUG: Palindromes response_data: {data['data']}") # DEBUG
    assert data["count"] == 2
    assert any(item["value"] == "nl_madam" for item in data["data"])
    assert any(item["value"] == "nl_level" for item in data["data"])

@pytest.mark.asyncio
async def test_delete_string_success(client: AsyncClient):
    await client.post("/strings", json={"value": "delete_me"})
    response = await client.delete("/strings/delete_me")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    response = await client.get("/strings/delete_me")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_string_not_found(client: AsyncClient):
    response = await client.delete("/strings/nonexistent_to_delete")
    assert response.status_code == 404
    response_data = response.json()
    assert "not found" in (response_data.get("detail") or response_data.get("value") or str(response_data))
