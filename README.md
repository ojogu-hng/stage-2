# Country Data API

## Overview
This project is a RESTful API built with Python and FastAPI, utilizing SQLAlchemy with asyncpg for asynchronous database operations. It fetches, caches, and serves comprehensive country and currency data from external sources.

## Features
- **FastAPI**: High-performance asynchronous web framework for building the API endpoints.
- **SQLAlchemy (Asyncio)**: Asynchronous object-relational mapper for robust and efficient database interactions with PostgreSQL.
- **Pydantic**: Data validation for request/response models and environment variable management.
- **AIOHTTP**: Asynchronous HTTP client used to efficiently fetch data from external REST APIs.
- **Pillow**: Python Imaging Library used for dynamically generating a summary image of the country data.

## Getting Started
### Installation
1.  **Clone the repository**
    ```bash
    git clone https://github.com/ojogu-hng/stage-2.git
    cd stage-2
    ```

2.  **Create and activate a virtual environment**
    ```bash
    # For Unix/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables**
    Create a `.env` file in the root directory and add the required variables.

5.  **Run the application**
    ```bash
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    The API will be available at `http://localhost:8000`.

### Environment Variables
You must create a `.env` file in the project's root directory.

- `DATABASE_URL`: The connection string for your PostgreSQL database.

**Example `.env` file:**
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/countries_db
```

## API Documentation
### Base URL
`http://localhost:8000`

### Endpoints
#### POST /countries/refresh
Refreshes the database with the latest country and currency data from external APIs. This operation can take some time.

**Request**:
No request body is required.

**Response**:
*   **Code**: `200 OK`
*   **Content**:
    ```json
    true
    ```

**Errors**:
- `503 Service Unavailable`: If an external API (Restcountries or Open ER) is unreachable.

---
#### GET /countries
Retrieves a list of all countries from the database. Supports filtering by region and currency, and sorting by GDP.

**Query Parameters**:
- `region` (optional, string): Filters countries by region (e.g., `Africa`).
- `currency` (optional, string): Filters countries by currency code (e.g., `NGN`).
- `sort` (optional, int): Set to `1` to sort countries by estimated GDP in descending order.

**Request**:
No request body is required.

**Response**:
*   **Code**: `200 OK`
*   **Content**:
    ```json
    [
        {
            "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "name": "Nigeria",
            "capital": "Abuja",
            "region": "Africa",
            "population": 206139587,
            "currency_code": "NGN",
            "exchange_rate": 411.5,
            "estimated_gdp": 310987654321.0,
            "flag_url": "https://restcountries.eu/data/nga.svg",
            "last_refreshed_at": "2024-09-15T10:30:00.123Z"
        }
    ]
    ```

**Errors**:
- This endpoint does not have specific error responses; it will return an empty array `[]` if no countries match the filter criteria.

---
#### GET /countries/image
Serves a dynamically generated PNG image summarizing the country data, including total countries and the top 5 by GDP.

**Request**:
No request body is required.

**Response**:
*   **Code**: `200 OK`
*   **Content-Type**: `image/png`
*   **Body**: A binary image file.

**Errors**:
- `404 Not Found`: If the summary image has not been generated yet (e.g., before the first `/countries/refresh` call).

---
#### GET /countries/{name}
Retrieves detailed information for a single country identified by its name.

**Request**:
No request body is required. The country name is passed as a URL path parameter.

**Response**:
*   **Code**: `200 OK`
*   **Content**:
    ```json
    {
        "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "name": "Nigeria",
        "capital": "Abuja",
        "region": "Africa",
        "population": 206139587,
        "currency_code": "NGN",
        "exchange_rate": 411.5,
        "estimated_gdp": 310987654321.0,
        "flag_url": "https://restcountries.eu/data/nga.svg",
        "last_refreshed_at": "2024-09-15T10:30:00.123Z"
    }
    ```

**Errors**:
- `404 Not Found`: If a country with the specified name does not exist in the database.

---
#### GET /status
Provides a status summary of the data stored in the database.

**Request**:
No request body is required.

**Response**:
*   **Code**: `200 OK`
*   **Content**:
    ```json
    {
        "total_countries": 195,
        "last_refreshed_at": "2024-09-15T10:30:00.123Z",
        "top_5": [
            987654321098.7,
            876543210987.6,
            765432109876.5,
            654321098765.4,
            543210987654.3
        ]
    }
    ```

**Errors**:
- This endpoint does not have specific error responses.

---
#### DELETE /countries/{name}
Deletes a country record from the database by its name.

**Request**:
No request body is required. The country name is passed as a URL path parameter.

**Response**:
*   **Code**: `200 OK`
*   **Content**:
    ```json
    {
        "message": "country 'Nigeria' deleted successfully."
    }
    ```

**Errors**:
- `404 Not Found`: If a country with the specified name does not exist in the database.

---
[![Readme was generated by Dokugen](https://img.shields.io/badge/Readme%20was%20generated%20by-Dokugen-brightgreen)](https://www.npmjs.com/package/dokugen)