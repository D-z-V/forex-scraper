import requests
import pandas as pd
from datetime import datetime, timedelta
import time

class ForexScraper:
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    class ScraperError(Exception):
        pass

    def _convert_to_unix_timestamp(self, date_str):
        """Convert date string to Unix timestamp."""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return int(time.mktime(date_obj.timetuple()))

    def get_currency_rates(self, from_currency, to_currency, start_date, end_date, interval='1d'):
        symbol = f"{from_currency}{to_currency}=X"
        period1 = self._convert_to_unix_timestamp(start_date)
        period2 = self._convert_to_unix_timestamp(end_date)
        params = {
            'period1': period1,
            'period2': period2,
            'interval': interval,
            'events': 'history',
            'includeAdjustedClose': 'true'
        }
        url = f"{self.base_url}{symbol}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result'] or 'timestamp' not in data['chart']['result'][0]:
                raise self.ScraperError(f"No data available for {symbol}")

            chart_data = data['chart']['result'][0]
            timestamps = chart_data['timestamp']
            quotes = chart_data['indicators']['quote'][0]
            
            # Create DataFrame with fetched data
            df = pd.DataFrame({
                'Date': pd.to_datetime(timestamps, unit='s'),
                'Open': quotes.get('open', []),
                'High': quotes.get('high', []),
                'Low': quotes.get('low', []),
                'Close': quotes.get('close', []),
                'Volume': quotes.get('volume', [])
            })
            
            # Drop rows with any NaN values
            df.dropna(inplace=True)
            
            return df
        except requests.exceptions.RequestException as e:
            raise self.ScraperError(f"Error fetching data: {str(e)}")
        except (KeyError, ValueError) as e:
            raise self.ScraperError(f"Error parsing data: {str(e)}")
