import aiohttp
import random
# Set up logger
from src.log import setup_logger
from src.schema import CountryApiResponse, CurrencyApiResponse
from src.db import Country, Currency
from sqlalchemy.ext.asyncio import AsyncSession
# from src.error import 
logger = setup_logger(__name__, "service.log")

class Service():
    def __init__(self, db:AsyncSession):
        self.db = db
    
    @staticmethod
    def compute_estimated_gdp(population, exchange_rate):
        random_factor = random.uniform(1000, 2000)
        return (population * random_factor) / exchange_rate
        
    async def _fetch_country_data(self):
        country_url = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
        logger.info(f"Fetching country data from {country_url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(country_url) as country_response:
                    country_response.raise_for_status()  # Raise an exception for bad status codes
                    country_data = await country_response.json()
            logger.info("Successfully fetched country data.")
            return country_data
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching country data: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching country data: {e}")
            raise

    async def _fetch_currency_data(self):
        currency_url = "https://open.er-api.com/v6/latest/USD"
        logger.info(f"Fetching currency data from {currency_url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(currency_url) as currency_response:
                    currency_response.raise_for_status()  # Raise an exception for bad status codes
                    currency_data = await currency_response.json()
            logger.info("Successfully fetched currency data.")
            return currency_data
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching currency data: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching currency data: {e}")
            raise

    
    async def fetch_rate(self, currency_symbol: str):
        logger.info(f"Fetching exchange rate for currency: {currency_symbol}")
        try:
            currency_data = await self._fetch_currency_data()
            validated_currency_data = CurrencyApiResponse(currency_data)
            rates:dict = validated_currency_data.rates
            rate = rates.get(currency_symbol)
            if rate:
                logger.info(f"Successfully fetched rate for {currency_symbol}: {rate}")
            else:
                logger.warning(f"Exchange rate for {currency_symbol} not found.")
            return rate
        except Exception as e:
            logger.error(f"Error fetching rate for {currency_symbol}: {e}")
            raise
        
        
    async def create_country(self):
        logger.info("Starting country data creation process.")
        try:
            country_data = await self._fetch_country_data()
            validated_country_data = CountryApiResponse.model_validate(country_data)
            logger.info("Country data validated successfully.")

            for country in validated_country_data.__root__:
                for currency in country.currencies:
                    logger.debug(f"Processing country: {country.name}, currency: {currency.symbol}")
                    exchange_rate = await self.fetch_rate(currency.symbol)
                    if exchange_rate is None:
                        logger.warning(f"Skipping {country.name} due to missing exchange rate for {currency.symbol}")
                        continue

                    estimated_gdp = Service.compute_estimated_gdp(country.population, exchange_rate)
                    logger.debug(f"Computed estimated GDP for {country.name}: {estimated_gdp}")

                    # write to db
                    stmt = Country(
                        name = country.name,
                        capital = country.capital,
                        region = country.region,
                        population = country.population,
                        currency_code = currency.symbol,
                        exchange_rate=exchange_rate,
                        estimated_gdp=estimated_gdp,
                        flag_url = country.flag,
                        independent = country.independent
                    )
                    self.db.add(stmt)
                    logger.info(f"Added {country.name} with currency {currency.symbol} to session.")
            await self.db.commit()
            logger.info("Successfully committed all country data to the database.")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error during country data creation: {e}")
            raise

    async def filter_country(self):
        pass
