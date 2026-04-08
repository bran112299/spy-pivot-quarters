from dataclasses import dataclass


@dataclass
class TradingViewSession:
    session_id: str
    auth_token: str
    user_id: str

    @staticmethod
    def create(response, cookies) -> 'TradingViewSession':
        session_id: str = cookies.get_dict()['sessionid']
        auth_token: str = response.json()['user']['auth_token']
        user_id: str = response.json()['user']['id']

        return TradingViewSession(
            session_id=session_id,
            auth_token=auth_token,
            user_id=user_id
        )

    @staticmethod
    def from_dict(d):
        return TradingViewSession(d['sessionid'], d['auth_token'], d['user_id'])

    def to_dict(self):
        return {
            'sessionid': self.session_id,
            'auth_token': self.auth_token,
            'user_id': self.user_id
        }
