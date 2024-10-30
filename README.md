# Forex History API

A FastAPI-based REST API that provides historical forex exchange rate data. The API scrapes data from Yahoo Finance, stores it in a SQLite database, and serves it through RESTful endpoints.

## Features

- Historical forex rates for currency pairs
- Automatic data caching in SQLite database
- Background job to keep data updated
- Support for multiple time periods (1W, 1M, 3M, 6M, 1Y)
- CORS enabled for cross-origin requests
- Rate limiting and caching for supported currencies

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- SQLite3

## Installation

1. Clone the repository:
```bash
git clone https://github.com/D-z-V/forex-scraper.git
cd forex-scraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with the following variables:
```bash
ALLOWED_ORIGINS=http://localhost:5173,http://yourfrontend.com  
```

## Project Structure

```
forex-history-api/
├── main.py
├── requirements.txt
├── services/
│   ├── __init__.py
│   ├── db.py
│   ├── scraper.py
│   └── cron_job.py
└── forex_data.db
```

## Running the Application

1. Start the API server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Access the API documentation at:
```
http://localhost:8000/docs
```

## API Endpoints

### GET /api/supported-currencies
Returns a list of supported currency codes and their full names.

Response:
```json
{
    "USD": "United States Dollar",
    "EUR": "Euro",
    "GBP": "British Pound Sterling",
    // ...
}
```

### POST /api/forex-data
Fetches historical forex data for a currency pair and time period.

Parameters:
- `from_currency`: Source currency code (e.g., "USD")
- `to_currency`: Target currency code (e.g., "EUR")
- `period`: Time period ("1W", "1M", "3M", "6M", "1Y")

Response:
```json
[
    {
        "date": "2024-01-01",
        "open_rate": 1.2345,
        "high_rate": 1.2400,
        "low_rate": 1.2300,
        "close_rate": 1.2350,
        "volume": 1000000
    },
    // ...
]
```

## Database Schema

The SQLite database contains a single table `forex_rates` with the following schema:

```sql
CREATE TABLE forex_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_currency TEXT,
    to_currency TEXT,
    date DATE,
    open_rate REAL,
    high_rate REAL,
    low_rate REAL,
    close_rate REAL,
    volume INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_currency, to_currency, date)
)
```

## Background Jobs

The application includes a background job (CronJob) that:
- Runs every 24 hours
- Updates historical data for configured currency pairs
- Fills in any missing data points
- Currently configured for GBP/INR and AED/INR pairs

## Error Handling

The API implements proper error handling for:
- Invalid currency codes
- Same source and target currencies
- Failed data fetching
- Database errors
- Rate limiting

## Development

To extend the supported currency pairs, modify the `pairs` list in the `CronJob` class:

```python
pairs = [
    ("GBP", "INR"),
    ("AED", "INR"),
    # Add more pairs here
]
```

## Production Deployment

For production deployment:

1. Set up a production-grade database:
```python
# Update DB connection in db.py
self.db_path = os.getenv('DATABASE_URL', 'forex_data.db')
```

2. Configure CORS properly:
```python
# Update in main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[your_frontend_domain],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

3. Use a production uvicorn server:
```bash
gunicorn -w 4 -k uvicorn app:app --host 0.0.0.0 --port $PORT
```
