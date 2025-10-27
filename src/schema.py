from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CountrySchema(BaseModel):
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
