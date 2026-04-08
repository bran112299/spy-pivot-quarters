import requests

from domain.trading_view.trading_view_session_repository import TradingViewSessionRepository
from infrastructure.persistence.trading_view_pickle_session_repository import TradingViewPickleSessionRepository
from infrastructure.tradingview.authentication.trading_view_session import TradingViewSession


class TradingViewAuthentifier:
    def __init__(self, repository: TradingViewSessionRepository = None):
        if repository is None:
            repository = TradingViewPickleSessionRepository()
        self.repository = repository

    def login(self, username: str, password: str) -> TradingViewSession:
        session = requests.Session()

        try:
            return self.repository.load_auth()
        except:
            print("Data not found, logging in...")
            sign_in_url = 'https://www.tradingview.com/accounts/signin/'
            data = {
                "username": username,
                "password": password,
                "remember": "on",
            }
            headers = {
                'Referer': 'https://www.tradingview.com',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
            }

            response = session.post(url=sign_in_url, data=data, headers=headers)
            print(response)

            try:
                session = TradingViewSession.create(
                    response=response,
                    cookies=session.cookies
                )
                self.repository.save_auth(
                    session=session
                )
            except:
                raise "Captcha required"

        return session
