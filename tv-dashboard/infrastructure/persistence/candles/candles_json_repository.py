import datetime
import json
import os

from src.domain.candles.candles import Candles
from src.domain.candles.candles_repository import CandlesRepository


class CandlesJsonRepository(CandlesRepository):
    def __init__(self, cache_path: str):
        self.cache_path: str = cache_path

    def save_candles(self, candles: Candles):
        candles_path = os.path.join(self.cache_path, 'candles', candles.get_symbol())
        if not os.path.exists(candles_path):
            os.makedirs(candles_path)

        file_name = '{}.json'.format(candles.get_end_date())
        json_path = os.path.join(candles_path, file_name)
        with open(json_path, 'w') as f:
            candles_json = candles.to_json()
            json.dump(candles_json, fp=f, indent=4)

    def get_candles(self, symbol: str, datetime_end: datetime.date) -> Candles:
        symbol = symbol.replace(':','-')
        candles_path = os.path.join(self.cache_path, 'candles', symbol)
        if not os.path.exists(candles_path):
            os.mkdir(candles_path)

        file_name = '{}.json'.format(datetime_end)
        json_path = os.path.join(candles_path, file_name)
        with open(json_path, 'r') as f:
            candles_json_str = json.load(f)
            return Candles.from_json(candles_json_str)
