import csv
import os
from typing import List

from src.domain.candles.candle import Candle
from src.domain.trading_view.trading_view_candles_repository import TradingViewCandlesRepository


class TradingViewCsvRepository(TradingViewCandlesRepository):
    def save(self, ticker: str, interval: str, candles: List[Candle]):
        ticker = ticker.replace(':', '-').strip('/') + f"({interval})"
        ticker_csv_path = os.path.join('cache', 'tickers', f"{ticker}-{interval}.csv")

        with open(ticker_csv_path, mode='w+', newline='') as data_file:
            csv_writer = csv.writer(data_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['close_time', 'open_time', 'open', 'high', 'low', 'close', 'volume'])

            for candle in candles:
                csv_writer.writerow([
                    candle.close_time,
                    candle.open_time,
                    candle.open,
                    candle.high,
                    candle.low,
                    candle.close,
                    candle.volume
                ])
