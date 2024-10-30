from apscheduler.schedulers.background import BackgroundScheduler
from services.scraper import ForexScraper
from services.db import DB

class CronJob:
    def __init__(self, db: DB, scraper: ForexScraper):
        print("Starting cron job...")
        self.db = db
        self.scraper = scraper
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.update_all_pairs, 'interval', hours=24)
        self.scheduler.start()

    def update_all_pairs(self):
        print("Updating all pairs...")
        pairs = [
            ("GBP", "INR"),
            ("AED", "INR")
        ]
        periods = ["1W", "1M", "3M", "6M", "1Y"]
        
        for from_currency, to_currency in pairs:
            for period in periods:
                start_date, end_date = self.db.get_period_dates(period)
                # data = self.db.fetch_from_db(from_currency, to_currency, start_date, end_date)
                print(f"Fetching data for {from_currency}-{to_currency} for period {period}... {start_date} to {end_date}")
                missing_ranges = self.db.fetch_missing_dates(from_currency, to_currency, start_date, end_date)
                if missing_ranges:
                    for start_missing, end_missing in missing_ranges:
                        df = self.scraper.get_currency_rates(
                            from_currency, to_currency,
                            start_missing.strftime('%Y-%m-%d'),
                            end_missing.strftime('%Y-%m-%d')
                        )
                        self.db.save_to_db(df, from_currency, to_currency)

    def shutdown(self):
        self.scheduler.shutdown()