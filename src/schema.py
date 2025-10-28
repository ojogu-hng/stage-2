from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CountryResponseSchema(BaseModel):
    id: int
    name: str
    capital: Optional[str] = None
    region: Optional[str] = None
    population: int
    currency_code: str
    exchange_rate: float
    estimated_gdp: float
    flag_url: Optional[str] = None
    last_refreshed_at: datetime

    class Config:
        from_attributes = True

class StatusSchema(BaseModel):
    total_countries: int
    last_refreshed_at: datetime

    class Config:
        from_attributes = True



class Currency(BaseModel):
    code: str = Field(..., pattern="^[A-Z]{3}$")
    name: str
    symbol: str

class CountryApiItem(BaseModel):
    name: str = Field(..., min_length=1)
    population: int = Field(..., ge=0)
    capital: Optional[str] = None
    region: Optional[str] = None
    currencies: list[Currency]
    flag: str
    independent: bool

class CountryApiResponse(BaseModel):
    __root__: list[CountryApiItem]

class CurrencyApiResponse(BaseModel):
    result: str
    provider: str
    documentation: str
    terms_of_use: str
    time_last_update_unix: int
    time_last_update_utc: str
    time_next_update_unix: int
    time_next_update_utc: str
    time_eol_unix: int
    base_code: str
    rates: dict[str, float]
