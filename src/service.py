import aiohttp
import random
from datetime import datetime
from src.schema import CountryApiResponse, CurrencyApiResponse
from src.db import Country, Currency, Status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
import sqlalchemy as sa # Added this import
from src.error import ServiceUnavailableError, NotFoundError
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
# Set up logger
from src.log import setup_logger, get_image_filepath
logger = setup_logger(__name__, "service.log")

class Service():
    def __init__(self, db:AsyncSession):
        self.db = db
    
    @staticmethod
    def compute_estimated_gdp(population, exchange_rate):
        logger.info(f"Computing estimated GDP for population={population}, exchange_rate={exchange_rate}")
        random_factor = random.uniform(1000, 2000)
        estimated_gdp = (population * random_factor) / exchange_rate
        logger.info(f"Calculated random_factor={random_factor}, estimated_gdp={estimated_gdp}")
        return estimated_gdp
        
    @staticmethod
    def generate_image(total_countries, top_5, last_refresh):
        logger.info(f"Generating image with total_countries={total_countries}, top_5={top_5}, last_refresh={last_refresh}")
        try:
            # Create a blank white image
            width, height = 800, 400
            image = Image.new("RGB", (width, height), color=(255, 255, 255)) 
            # Initialize draw context
            draw = ImageDraw.Draw(image)
            # Optional: Load a TrueType font (if you have one)
            # font = ImageFont.truetype("arial.ttf", 24)
            # fallback font:
            font = ImageFont.load_default()
            
            # Add text dynamically
            draw.text((50, 120), f"Total number of countries: {total_countries}", fill="black", font=font)
            draw.text((50, 120), f"top 5 countries  by estimated GDP: {top_5}", fill="black", font=font)
            draw.text((50, 120), f"Timestamp of last refresh: {last_refresh}", fill="black", font=font)
            
            file_path = get_image_filepath("image.png")
            logger.info(f"Saving generated image to: {file_path}")
            image.save(file_path)
            logger.info("Image generated and saved successfully.")
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            raise
        
    
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
            raise ServiceUnavailableError(f"Could not fetch data from Restcountries API: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching country data: {e}")
            raise ServiceUnavailableError(f"An unexpected error occurred with Restcountries API: {e}")

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
            raise ServiceUnavailableError(f"Could not fetch data from Open ER API: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching currency data: {e}")
            raise ServiceUnavailableError(f"An unexpected error occurred with Open ER API: {e}")

    
    async def fetch_rate(self, currency_code: str):
        logger.info(f"Fetching exchange rate for currency: {currency_code}")
        try:
            currency_data = await self._fetch_currency_data()
            validated_currency_data = CurrencyApiResponse.model_validate(currency_data)
            rates:dict = validated_currency_data.rates
            rate = rates.get(currency_code)
            if rate:
                logger.info(f"Successfully fetched rate for {currency_code}: {rate}")
            else:
                logger.warning(f"Exchange rate for {currency_code} not found.")
            return rate
        except Exception as e:
            logger.error(f"Error fetching rate for {currency_code}: {e}")
            raise
        
    async def filter_search(self, region:Optional[str]=None,
    currency:Optional[str]=None, 
    sort:Optional[int]=None):
        logger.info(f"Filtering search with region='{region}', currency='{currency}', sort='{sort}'")
        try:
            stmt = select(Country)
            if region is not None:
                stmt = stmt.where(Country.region == region)
                logger.debug(f"Applied region filter: {region}")
            if currency is not None:
                stmt = stmt.where(Country.currency_code == currency)
                logger.debug(f"Applied currency filter: {currency}")
            if sort is not None:
                stmt = stmt.order_by(sa.desc(Country.estimated_gdp))
                logger.debug(f"Applied sort order by estimated_gdp: {sort}")
            
            result = await self.db.execute(stmt)
            country = result.scalars().all()
            logger.info(f"Found {len(country)} countries matching criteria.")
            return country
        except Exception as e:
            logger.error(f"Error during filter search: {e}")
            raise
      
    async def create_country(self):
        logger.info("Starting country data creation process.")
        try:
            country_data = await self._fetch_country_data()
            validated_country_data = CountryApiResponse.model_validate(country_data)
            logger.info(f"Country data validated successfully. {validated_country_data}")

            for country_api_data in validated_country_data.model_dump():
                country_name = country_api_data["name"]
                logger.info(f"Processing country: {country_name}")

                # Skip countries without currency
                if not country_api_data.get("currencies"):
                    logger.warning(f"Country does not have currency: {country_name}. Skipping.")
                    continue

                for currency in country_api_data.get("currencies"):
                    currency_code = currency["code"]
                    exchange_rate = await self.fetch_rate(currency_code)

                    if exchange_rate is None:
                        logger.warning(f"Skipping {country_name} due to missing exchange rate for {currency_code}")
                        continue

                    estimated_gdp = Service.compute_estimated_gdp(
                        country_api_data["population"], exchange_rate
                    )
                    logger.debug(f"Computed estimated GDP for {country_name}: {estimated_gdp}")

                    #  UPSERT: insert or update if exists
                    stmt = insert(Country).values(
                        name=country_name,
                        capital=country_api_data["capital"],
                        region=country_api_data["region"],
                        population=country_api_data["population"],
                        currency_code=currency_code,
                        exchange_rate=exchange_rate,
                        estimated_gdp=estimated_gdp,
                        flag_url=country_api_data["flag"],
                        independent=country_api_data["independent"],
                        last_refreshed_at=datetime.now()
                    )

                    stmt = stmt.on_conflict_do_update(
                        index_elements=[Country.name],  # column with UNIQUE constraint
                        set_={
                            "capital": stmt.excluded.capital,
                            "region": stmt.excluded.region,
                            "population": stmt.excluded.population,
                            "currency_code": stmt.excluded.currency_code,
                            "exchange_rate": stmt.excluded.exchange_rate,
                            "estimated_gdp": stmt.excluded.estimated_gdp,
                            "flag_url": stmt.excluded.flag_url,
                            "independent": stmt.excluded.independent,
                            "last_refreshed_at": datetime.now(),
                        },
                    )

                    await self.db.execute(stmt)
                    logger.info(f"Upserted {country_name} with currency {currency_code}.")

            # Update or insert status record
            now = datetime.now()
            stmt_status = insert(Status).values(last_refreshed_at=now)
            stmt_status = stmt_status.on_conflict_do_update(
                index_elements=[Status.id],  # assumes 'id' is unique
                set_={"last_refreshed_at": now}
            )
            await self.db.execute(stmt_status)
            logger.info("Updated or created global last_refreshed_at timestamp.")

            await self.db.commit()
            logger.info("Successfully committed all country data and updated status to the database.")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error during country data creation: {e}")
            raise
        
    async def status(self):
        logger.info("Fetching application status.")
        try:
            count = await self.db.execute(
                select(sa.func.count(Country.name))
            )
            total_countries = count.scalar()#return the single value 
            
            # Fetch the last_refreshed_at from the Status table
            status_record = await self.db.execute(select(Status).where(Status.id == 1)) # Assuming id=1 for the single status record
            last_refreshed_at_obj = status_record.scalar_one_or_none()
            last_refreshed_at = last_refreshed_at_obj.last_refreshed_at if last_refreshed_at_obj else None

            logger.info(f"Status fetched: total_countries={total_countries}, last_refreshed_at={last_refreshed_at}")
            return {
                "total_countries": total_countries,
                "last_refreshed_at": last_refreshed_at
            } 
        except Exception as e:
            logger.error(f"Error fetching application status: {e}")
            raise
    
    async def fetch_by_name(self, name):
        logger.info(f"Fetching country by name: {name}")
        try:
            result = await self.db.execute(
                select(Country).where(Country.name == name)
            )
            country = result.scalar_one_or_none()
            if country:
                logger.info(f"Found country: {name}")
            else:
                logger.info(f"Country not found: {name}")
            return country
        except Exception as e:
            logger.error(f"Error fetching country by name '{name}': {e}")
            raise

    async def delete_country(self, name):
        logger.info(f"Attempting to delete country: {name}")
        try:
            country = await self.fetch_by_name(name)
            if not country:
                logger.warning(f"Country not found for deletion: {name}")
                raise NotFoundError(f"Country with name {name} not found.")
            await self.db.delete(country)
            await self.db.commit() # Changed self.commit() to self.db.commit()
            logger.info(f"Successfully deleted country: {name}")
        except NotFoundError:
            raise # Re-raise NotFoundError as it's an expected business error
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting country '{name}': {e}")
            raise
