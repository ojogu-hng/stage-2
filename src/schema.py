from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, RootModel
from uuid import UUID

class CountryResponseSchema(BaseModel):
    id: UUID
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
    code: Optional[str] =None
    name: Optional[str] = None
    symbol: Optional[str] = None

class CountryApiItem(BaseModel):
    name: str = Field(..., min_length=1)
    population: int = Field(..., ge=0)
    capital: Optional[str] = None
    region: Optional[str] = None
    currencies: Optional[list[Currency]] = None
    flag: str
    independent: bool

class CountryApiResponse(RootModel[list[CountryApiItem]]):
    # A “root model” is a model that wraps a single value — usually a list, dict, or primitive — instead of having multiple fields
    pass 

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
