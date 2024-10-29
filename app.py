from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from db import DB
from scraper import ForexScraper
from cron_job import CronJob

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

@app.post("/api/forex-data")
async def get_forex_data(from_currency: str, to_currency: str, period: str) -> List[ForexResponse]:
    print(f"Fetching data for {from_currency}-{to_currency} for period {period}...")
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
        
        # Re-fetch the complete range to include newly saved data
        data = db.fetch_from_db(from_currency, to_currency, start_date, end_date)
    
    return [ForexResponse(**row) for row in data]



@app.on_event("shutdown")
def shutdown_event():
    cron_job.shutdown()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
