import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from functools import lru_cache

from services.db import DB
from services.scraper import ForexScraper
from services.cron_job import CronJob

app = FastAPI(title="Forex History API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = ForexScraper()
db = DB()
cron_job = CronJob(db, scraper)

class ForexResponse(BaseModel):
    date: str
    open_rate: float
    high_rate: float
    low_rate: float
    close_rate: float
    volume: int

@lru_cache()
def fetch_supported_currencies():
    url = "https://query1.finance.yahoo.com/v1/finance/currencies"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch currency data")
    
    data = response.json()
    supported_currencies = {currency['shortName']: currency['longName'] for currency in data['currencies']['result']}
    return supported_currencies

@app.get("/api/supported-currencies")
async def get_supported_currencies() -> dict:
    return fetch_supported_currencies()

@app.post("/api/forex-data")
async def get_forex_data(from_currency: str, to_currency: str, period: str) -> List[ForexResponse]:

    supported_currencies = fetch_supported_currencies()
    if from_currency not in supported_currencies:
        raise HTTPException(status_code=400, detail=f"{from_currency} is not a valid currency code.")
    if to_currency not in supported_currencies:
        raise HTTPException(status_code=400, detail=f"{to_currency} is not a valid currency code.")
    
    if from_currency == to_currency:
        raise HTTPException(status_code=400, detail="From and To currencies cannot be the same.")

    start_date, end_date = db.get_period_dates(period)
    data = db.fetch_from_db(from_currency, to_currency, start_date, end_date)

    missing_ranges = db.fetch_missing_dates(from_currency, to_currency, start_date, end_date)
    if missing_ranges:
        for start_missing, end_missing in missing_ranges:
            df = scraper.get_currency_rates(
                from_currency, to_currency,
                start_missing.strftime('%Y-%m-%d'),
                end_missing.strftime('%Y-%m-%d')
            )
            db.save_to_db(df, from_currency, to_currency)

        data = db.fetch_from_db(from_currency, to_currency, start_date, end_date)
    
    return [ForexResponse(**row) for row in data]

@app.on_event("shutdown")
def shutdown_event():
    cron_job.shutdown()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
