import requests

get_chart_token_url = 'https://www.tradingview.com/chart-token/?image_url={}&user_id={}'


class TradingViewJwtClient:
    def get_chart_token(
            self,
            layout_id: str,
            symbol: str,
            user_id: str,
            session_id: str
    ):
        chart_token_url = get_chart_token_url.format(layout_id, user_id)
        print(chart_token_url)
        jwt_response = requests.get(
            chart_token_url,
            headers={
                "Cookie": 'sessionid={}'.format(session_id),
                'Referer': 'https://www.tradingview.com/chart/{}/?symbol={}'.format(
                    layout_id, symbol), 'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': 'Linux',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        })

        jwt_json = jwt_response.json()
        print(jwt_json)
        return jwt_json['token']
