from contextlib import asynccontextmanager
from typing import Optional
from src.service import Service
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import drop_db, get_session, init_db
from src.error import NotFoundError, register_error_handler


@asynccontextmanager
async def life_span(app: FastAPI):
    # Startup
    try:
        # await drop_db()
        # print("tables dropped")
        await init_db()
        print("tables created")
    except Exception as e:
        print(f"Error during database initialization: {str(e)}")
        raise

    yield  # Application is running

    # Shutdown
    print("server is ending.....")


app = FastAPI(lifespan=life_span)

# register errors
register_error_handler(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def get_service(db: AsyncSession = Depends(get_session)):
    return Service(db=db)


@app.post("/countries/refresh", status_code=201)
# Fetch all countries and exchange rates, then cache them in the database
async def fetch_Countries_data():
    pass 

# IMPORTANT: /strings route MUST come BEFORE /strings/{string_value}. query param should come before path param

@app.get("/countries") 
#Get all countries from the DB (support filters and sorting) - ?region=Africa | ?currency=NGN | ?sort=gdp_desc
async def get_countries_filter():
    pass



@app.get("/countries/{name}")
# Get one country by name
async def get_country():
    pass




@app.get("/status ")
#  Show total countries and last refresh timestamp
async def status():
    pass 

@app.get("/countries/image ")
#   serve summary image
async def country_image():
    pass 



@app.delete("/countries/{name}")
#Delete a country record
async def delete_country():
    pass



