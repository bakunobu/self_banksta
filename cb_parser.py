# cbr_parser.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CBRKeyRateParser:
    URL = "https://www.cbr.ru/hd_base/keyrate/"

    @staticmethod
    def _parse_date(date_str: str) -> datetime.date:
        """Convert CBR date format (e.g. '12.02.2025') to Python date"""
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()

    @classmethod
    def get_latest_rate(cls) -> dict:
        """
        Fetch the latest key rate from CBR website.
        
        Returns:
            dict: {"date": date, "rate": float}
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(cls.URL, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the main table (usually the first one)
            table = soup.find("table", class_="data")
            if not table:
                raise ValueError("Could not find key rate table on the page")

            # Get first row of data (most recent)
            first_row = table.find("tr", class_="item")
            if not first_row:
                raise ValueError("No data rows found in the table")

            cells = first_row.find_all("td")
            if len(cells) < 2:
                raise ValueError("Unexpected table structure")

            raw_date = cells[0].get_text()
            raw_rate = cells[1].get_text()

            rate_date = cls._parse_date(raw_date)
            key_rate = float(raw_rate.replace(',', '.'))  # Convert comma decimal to float

            logger.info(f"Latest CBR key rate: {key_rate}% on {rate_date}")

            return {"date": rate_date, "rate": key_rate}

        except Exception as e:
            logger.error(f"Error fetching CBR key rate: {e}")
            raise

    @classmethod
    def get_historical_rates(cls, limit: int = None) -> list:
        """
        Fetch historical key rates.
        
        Args:
            limit: Max number of records to return (None = all)
        
        Returns:
            List of dicts: [{"date": date, "rate": float}, ...]
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(cls.URL, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find("table", class_="data")
            rows = table.find_all("tr", class_="item")

            history = []
            for row in rows[:limit]:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    raw_date = cells[0].get_text()
                    raw_rate = cells[1].get_text()
                    history.append({
                        "date": cls._parse_date(raw_date),
                        "rate": float(raw_rate.replace(',', '.'))
                    })

            logger.info(f"Fetched {len(history)} historical key rate records")
            return history

        except Exception as e:
            logger.error(f"Error fetching historical CBR key rates: {e}")
            raise