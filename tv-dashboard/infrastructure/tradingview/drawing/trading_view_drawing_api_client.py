import datetime
import json
import time
from typing import Dict, Optional, List

import requests

from config import owner_source
from domain.trends.trend import Trend
from infrastructure.tradingview.drawing.trading_view_id_generator import TradingViewIdGenerator
from infrastructure.tradingview.drawing.trading_view_request_parameters import TradingViewRequestParameters
from infrastructure.tradingview.time_frames.trading_view_time_frame import TradingViewTimeFrame
from infrastructure.tradingview.trends.trend_converter import TradingViewTrendConverter

edit_chart_url = 'https://charts-storage.tradingview.com/charts-storage/layout/{}/sources?chart_id={}&jwt={}'

from concurrent.futures import ThreadPoolExecutor
from concurrent import futures


class TradingViewDrawingApiClient:
    def __init__(
            self,
            parameters: TradingViewRequestParameters,
            trading_view_id_generator: TradingViewIdGenerator,
            trading_view_trend_converter: TradingViewTrendConverter
    ):
        self.trading_view_id_generator = trading_view_id_generator
        self.parameters: TradingViewRequestParameters = parameters
        self.trading_view_trend_converter: TradingViewTrendConverter = trading_view_trend_converter

        self.url = edit_chart_url.format(self.parameters.layout_id, self.parameters.chart_id, self.parameters.jwt)

    def get_drawings(self, symbol='BINANCE:BTCUSDTPERP', drawing_type: Optional[str] = None):
        url = edit_chart_url.format(self.parameters.layout_id, self.parameters.chart_id, self.parameters.jwt)
        drawing_response = requests.get(url, headers=self.create_headers(symbol))
        drawing_json = drawing_response.json()

        drawings = {}
        for source_id, source in drawing_json['payload']['sources'].items():
            if source['symbol'] != symbol:
                continue
            drawings[source_id] = source

        return drawings

    def remove_everything(self, symbol='BINANCE:BTCUSDTPERP', drawing_type: Optional[str] = None):
        url = edit_chart_url.format(self.parameters.layout_id, self.parameters.chart_id, self.parameters.jwt)
        drawing_response = requests.get(url, headers=self.create_headers(symbol))
        drawing_json = drawing_response.json()
        null_sources_dict = {}
        for source_id, source in drawing_json['payload']['sources'].items():
            if source['symbol'] != symbol:
                continue

            if drawing_type is None or source['state']['type'] != drawing_type:
                null_sources_dict[source_id] = None

        body = {
            "sources": null_sources_dict
        }
        url = edit_chart_url.format(self.parameters.layout_id, self.parameters.chart_id, self.parameters.jwt)
        return requests.put(url, json.dumps(body), headers=self.create_headers(symbol))

    def draw_vertical_ray(
            self,
            symbol: str,
            time_t: int,
            text: str,
            line_color: str,
            line_style=0,
            line_width=1,
            vertical_label_align="middle",
            title: str = '',
            drawing_group: Dict = None,
            font_size=10,
    ):
        figure_type = 'LineToolVertLine'
        source_id = self.trading_view_id_generator.create_source_id()
        link_key = self.trading_view_id_generator.create_link_key()
        text_color = "rgba(255, 255, 255, 1)"

        body = {
            "drawing_groups": {
                drawing_group['id']: drawing_group
            },
            "clientId": self.parameters.client_id,
            "sources": {
                source_id: {
                    "id": source_id,
                    "groupId": drawing_group['id'],
                    "ownerSource": self.parameters.owner_source,
                    "state": {
                        "type": figure_type, "id": source_id,
                        "state": {
                            "linecolor": line_color,
                            "linewidth": line_width,
                            "linestyle": line_style,
                            "showLabel": True,
                            "textcolor": text_color,
                            "lastUpdateTime": round(time.time()),
                            "extendLine": True,
                            "showTime": True,
                            "horzLabelsAlign": "center",
                            "vertLabelsAlign": vertical_label_align,
                            "textOrientation": "horizontal",
                            "fontsize": font_size,
                            "bold": True,
                            "italic": False,
                            "symbolStateVersion": 2,
                            "zOrderVersion": 2,
                            "visible": True,
                            "frozen": False,
                            "symbol": symbol,
                            "unitId": None,
                            "title": title if len(title) > 0 else text,
                            "text": text,
                            "interval": TradingViewTimeFrame.TF_1M.value
                        },
                        "points": [{"time_t": time_t, "offset": 0, "price": 0}],
                        "zorder": -278,
                        "ownerSource": self.parameters.owner_source,
                        "linkKey": link_key
                    },
                    "symbol": symbol,
                    "unitId": None
                }},
        }

        response = requests.put(self.url, json.dumps(body), headers=self.create_headers(symbol))
        print(response)

        return body

    def draw_path(
            self,
            points: List,  # [{time_t, offset, price}]
            line_color: str,
            drawing_group: Dict = None,
            symbol='BINANCE:BTCUSDTPERP',
            title: str = '',
            text: str = '',
            line_style: int = 0,
            line_width: int = 1,
            font_size: int = 12,
            send_request: bool = False,
            visibility: Dict = None,
            vertical_labels_align: str = "bottom"
    ):
        if visibility is None:
            visibility = {}
        source_id = self.trading_view_id_generator.create_source_id()
        link_key = self.trading_view_id_generator.create_link_key()

        body = {
            "drawing_groups": {
            },
            "clientId": self.parameters.client_id,
            "sources": {
                source_id: {
                    "currencyId": None,
                    "id": source_id,
                    "ownerSource": owner_source,
                    "state": {
                        "id": source_id,
                        "ownerSource": owner_source,
                        "points": points,
                        "type": "LineToolPath",
                        "state": {
                            "lineColor": line_color,
                            "lineWidth": line_width,
                            "lineStyle": 0,
                            "leftEnd": 0,
                            "rightEnd": 1,
                            "linecolor": line_color,
                            "linewidth": line_width,
                            "linestyle": 2,
                            "showPrice": True,
                            "showLabel": True,
                            "textcolor": "rgba(255, 255, 255, 1)",
                            "fontsize": 12,
                            "bold": True,
                            "italic": True,
                            "horzLabelsAlign": "right",
                            "vertLabelsAlign": "bottom",
                            "fixedSize": True,
                            "text": "",
                            "symbolStateVersion": 2,
                            "zOrderVersion": 2,
                            "visible": True,
                            "frozen": False,
                            "symbol": symbol,
                            "currencyId": None,
                            "unitId": None,
                            "title": title,
                            "interval": "1M"
                        },
                        "zorder": -70
                    },
                    "symbol": symbol,
                    "unitId": None
                }
            }
        }
        if send_request:
            response = requests.put(self.url, json.dumps(body), headers=self.create_headers(symbol))
            print(response)
        return body

    def draw_horizontal_ray(
            self,
            time_t: int,
            price: float,
            drawing_group: Dict,
            line_color: str,
            symbol='BINANCE:BTCUSDTPERP',
            text: str = '',
            line_style: int = 0,
            line_width: int = 1,
            font_size: int = 12,
            send_request: bool = False,
            visibility: Dict = None,
            vertical_labels_align: str = "bottom"
    ):
        if visibility is None:
            visibility = {}
        figure_type = 'LineToolHorzRay'
        source_id = self.trading_view_id_generator.create_source_id()
        link_key = self.trading_view_id_generator.create_link_key()
        text_color = "rgba(255, 255, 255, 1)"

        body = {
            "drawing_groups": {
                drawing_group['id']: drawing_group
            },
            "clientId": self.parameters.client_id,
            "sources": {
                source_id: {
                    "id": source_id,
                    "groupId": drawing_group['id'],
                    "ownerSource": self.parameters.owner_source,
                    "state": {
                        "type": figure_type, "id": source_id,
                        "state": {
                            "linecolor": line_color,
                            "linewidth": line_width,
                            "linestyle": line_style,
                            "showPrice": True,
                            "showLabel": True,
                            "textcolor": text_color,
                            "fontsize": font_size,
                            "bold": True,
                            "italic": True,
                            "horzLabelsAlign": "right",
                            "vertLabelsAlign": vertical_labels_align,
                            "lastUpdateTime": round(time.time()),
                            "fixedSize": True,
                            "symbolStateVersion": 2,
                            "zOrderVersion": 2,
                            "visible": True,
                            "frozen": False,
                            "symbol": symbol,
                            "unitId": None,
                            "title": "",
                            "text": text,
                            "interval": TradingViewTimeFrame.TF_1M.value,
                            "intervalsVisibilities": visibility
                        },
                        "points": [
                            {"time_t": time_t, "offset": 0, "price": price}
                        ],
                        "zorder": -0.032,
                        "ownerSource": self.parameters.owner_source, "linkKey": link_key
                    },
                    "symbol": symbol,
                    "unitId": None
                }},
        }

        if send_request:
            headers = self.create_headers(symbol)
            return requests.put(self.url, json.dumps(body), headers=headers)
        return body

    def send_requests(self, symbol: str, drawing_requests, multithreading=True):
        if multithreading:
            processes = []
            for body in drawing_requests:
                with ThreadPoolExecutor(max_workers=None) as executor:
                    processes.append(
                        executor.submit(requests.put, self.url, json.dumps(body), headers=self.create_headers(symbol)))

            for job in futures.as_completed(processes):
                result_done = job.result()
                if result_done == "<Response [503]>":
                    print(result_done, type(result_done))

        else:
            for body in drawing_requests:
                requests.put(self.url, json.dumps(body), headers=self.create_headers(symbol))
        return

    def draw_line(
            self,
            point_one,
            point_two,
            drawing_group: Dict,
            line_color: str,
            symbol='BINANCE:BTCUSDTPERP',
            text: str = '',
            line_style: int = 0,
            line_width: int = 1
    ):
        figure_type = 'LineToolHorzRay'
        source_id = self.trading_view_id_generator.create_source_id()
        link_key = self.trading_view_id_generator.create_link_key()
        text_color = "rgba(255, 255, 255, 1)"

        body = {
            "drawing_groups": {drawing_group['id']: drawing_group},
            "clientId": self.parameters.client_id,
            "sources": {
                "XxBVji": {
                    "id": source_id,
                    "ownerSource": self.parameters.owner_source,
                    "state": {
                        "type": "LineToolTrendLine",
                        "id": source_id,
                        "state": {
                            "linecolor": line_color,
                            "linewidth": line_width,
                            "linestyle": line_style,
                            "extendLeft": False,
                            "extendRight": False,
                            "leftEnd": 0,
                            "rightEnd": 0,
                            "showLabel": True,
                            "horzLabelsAlign": "center",
                            "vertLabelsAlign": "bottom",
                            "textcolor": text_color,
                            "fontsize": 11,
                            "bold": False,
                            "italic": False,
                            "alwaysShowStats": False,
                            "showMiddlePoint": False,
                            "showPriceLabels": False,
                            "showPriceRange": True,
                            "showBarsRange": False,
                            "showDateTimeRange": False,
                            "showDistance": True,
                            "showAngle": False,
                            "statsPosition": 2,
                            "fixedSize": True,
                            "symbolStateVersion": 2,
                            "zOrderVersion": 2,
                            "visible": True,
                            "frozen": False,
                            "symbol": symbol,
                            "unitId": None,
                            "title": "",
                            "text": text,
                            "interval": TradingViewTimeFrame.TF_1M.value
                        },
                        "points": [
                            {"time_t": point_one['time_t'], "offset": 0, "price": point_one['price']},
                            {"time_t": point_two['time_t'], "offset": 0, "price": point_two['price']}
                        ],
                        "zorder": -10000.012,
                        "ownerSource": self.parameters.owner_source,
                        "linkKey": link_key
                    },
                    "symbol": symbol,
                    "unitId": None
                }
            }
        }

        return requests.put(self.url, json.dumps(body), headers=self.create_headers(symbol))

    def draw_line_tool_trend_line_from_points(
            self,
            points,
            line_color: str,
            line_style: int,
            line_width: int,
            drawing_group: Dict,
            symbol='BINANCE:BTCUSDTPERP'
    ):
        figure_type = "LineToolTrendLine"

        source_id = self.trading_view_id_generator.create_source_id()
        link_key = self.trading_view_id_generator.create_link_key()
        text_color = "rgba(255, 255, 255, 1)"

        return requests.put(
            edit_chart_url.format(self.parameters.layout_id, self.parameters.chart_id, self.parameters.jwt),
            json.dumps({
                "drawing_groups": {
                    drawing_group['id']: drawing_group
                },
                "clientId": self.parameters.client_id,
                "sources": {
                    source_id: {
                        "id": source_id,
                        "groupId": drawing_group['id'],
                        "ownerSource": self.parameters.owner_source,
                        "state": {
                            "type": figure_type,
                            "id": source_id,
                            "state": {
                                "linecolor": line_color,
                                "linewidth": line_width,
                                "linestyle": line_style,
                                "extendLeft": False,
                                "extendRight": True,
                                "leftEnd": 0,
                                "rightEnd": 0,
                                "showLabel": True,
                                "horzLabelsAlign": "right",
                                "vertLabelsAlign": "top",
                                "textcolor": text_color,
                                "fontsize": 10,
                                "bold": True,
                                "italic": False,
                                "alwaysShowStats": False,
                                "showMiddlePoint": False,
                                "showPriceLabels": False,
                                "showPriceRange": None,
                                "showBarsRange": False,
                                "showDateTimeRange": None,
                                "showDistance": False,
                                "showAngle": None,
                                "statsPosition": 2,
                                "fixedSize": False,
                                "symbolStateVersion": 2,
                                "zOrderVersion": 2,
                                "visible": True,
                                "frozen": False,
                                "symbol": symbol,
                                "unitId": None,
                                "title": "",
                                "text": "",
                                "interval": TradingViewTimeFrame.TF_1M.value
                            },
                            "points": points,
                            "zorder": -10,
                            "ownerSource": self.parameters.owner_source,
                            "linkKey": link_key
                        },
                        "symbol": symbol,
                        "unitId": "APZ"
                    }},
            }), headers=self.create_headers(symbol))

    def draw_trend(
            self,
            trend: Trend,
            line_color: str,
            line_style: int,
            line_width: int,
            drawing_group: Dict,
            symbol='BINANCE:BTCUSDTPERP'
    ):
        points = self.trading_view_trend_converter.get_trading_view_points_from_trend(trend)
        figure_type = "LineToolRay"

        source_id = self.trading_view_id_generator.create_source_id()
        link_key = self.trading_view_id_generator.create_link_key()
        text_color = "rgba(255, 255, 255, 1)"

        return requests.put(
            edit_chart_url.format(self.parameters.layout_id, self.parameters.chart_id, self.parameters.jwt),
            json.dumps({
                "drawing_groups": {
                    drawing_group['id']: drawing_group
                },
                "clientId": self.parameters.client_id,
                "sources": {
                    source_id: {
                        "id": source_id,
                        "groupId": drawing_group['id'],
                        "ownerSource": self.parameters.owner_source,
                        "state": {
                            "type": figure_type,
                            "id": source_id,
                            "state": {
                                "linecolor": line_color,
                                "linewidth": line_width,
                                "linestyle": line_style,
                                "extendLeft": False,
                                "extendRight": True,
                                "leftEnd": 0,
                                "rightEnd": 0,
                                "showLabel": True,
                                "horzLabelsAlign": "right",
                                "vertLabelsAlign": "top",
                                "textcolor": text_color,
                                "fontsize": 10,
                                "bold": True,
                                "italic": False,
                                "alwaysShowStats": False,
                                "showMiddlePoint": False,
                                "showPriceLabels": False,
                                "showPriceRange": None,
                                "showBarsRange": False,
                                "showDateTimeRange": None,
                                "showDistance": False,
                                "showAngle": None,
                                "statsPosition": 2,
                                "fixedSize": False,
                                "symbolStateVersion": 2,
                                "zOrderVersion": 2,
                                "visible": True,
                                "frozen": False,
                                "symbol": symbol,
                                "unitId": None,
                                "title": "",
                                "text": "",
                                "interval": TradingViewTimeFrame.TF_1M.value
                            },
                            "points": points,
                            "zorder": -10,
                            "ownerSource": self.parameters.owner_source,
                            "linkKey": link_key
                        },
                        "symbol": symbol,
                        "unitId": None
                    }},
            }), headers=self.create_headers(symbol))

    def draw_line_tool_ray(
            self,
            price_1,
            time_1,
            price_2,
            time_2,
            title: str,
            line_color: str,
            line_style: int,
            line_width: int,
            drawing_group: Dict,
            text: str = '',
            symbol='BINANCE:BTCUSDTPERP'
    ):
        points = [
            {
                'price': price_1,
                'time_t': round(time_1.timestamp()),
                'offset': 0
            },
            {
                'price': price_2,
                'time_t': round(time_2.timestamp()),
                'offset': 0
            }
        ]
        figure_type = "LineToolRay"

        source_id = self.trading_view_id_generator.create_source_id()
        link_key = self.trading_view_id_generator.create_link_key()
        text_color = "rgba(255, 255, 255, 1)"

        return requests.put(
            edit_chart_url.format(self.parameters.layout_id, self.parameters.chart_id, self.parameters.jwt),
            json.dumps({
                "drawing_groups": {
                    drawing_group['id']: drawing_group
                },
                "clientId": self.parameters.client_id,
                "sources": {
                    source_id: {
                        "id": source_id,
                        "groupId": drawing_group['id'],
                        "ownerSource": self.parameters.owner_source,
                        "state": {
                            "type": figure_type,
                            "id": source_id,
                            "state": {
                                "linecolor": line_color,
                                "linewidth": line_width,
                                "linestyle": line_style,
                                "extendLeft": False,
                                "extendRight": True,
                                "leftEnd": 0,
                                "rightEnd": 0,
                                "showLabel": True,
                                "horzLabelsAlign": "right",
                                "vertLabelsAlign": "top",
                                "textcolor": text_color,
                                "fontsize": 10,
                                "bold": True,
                                "italic": False,
                                "alwaysShowStats": False,
                                "showMiddlePoint": False,
                                "showPriceLabels": False,
                                "showPriceRange": None,
                                "showBarsRange": False,
                                "showDateTimeRange": None,
                                "showDistance": False,
                                "showAngle": None,
                                "statsPosition": 2,
                                "fixedSize": False,
                                "symbolStateVersion": 2,
                                "zOrderVersion": 2,
                                "visible": True,
                                "frozen": False,
                                "symbol": symbol,
                                "unitId": None,
                                "title": title,
                                "text": text,
                                "interval": TradingViewTimeFrame.TF_1M.value
                            },
                            "points": points,
                            "zorder": -10,
                            "ownerSource": self.parameters.owner_source,
                            "linkKey": link_key
                        },
                        "symbol": symbol,
                        "unitId": None
                    }},
            }), headers=self.create_headers(symbol))
    def draw_box(
            self,
            point_one,
            point_two,
            is_long: bool,
            color: str,
            background_color: str,
            drawing_group: Dict,
            text: str = '',
            symbol='BINANCE:BTCUSDTPERP'
    ):
        link_key = self.trading_view_id_generator.create_link_key()
        source_id = self.trading_view_id_generator.create_source_id()

        body = json.dumps({
            "sources": {
                source_id: {
                    "id": source_id,
                    "ownerSource": self.parameters.owner_source,
                    "groupId": drawing_group['id'],
                    "state": {
                        "type": "LineToolRectangle",
                        "id": source_id,
                        "state": {
                            "color": color,
                            "fillBackground": True,
                            "backgroundColor": background_color,
                            "linewidth": 2,
                            "transparency": 10,
                            "showLabel": True,
                            "horzLabelsAlign": "left",
                            "vertLabelsAlign": "bottom" if is_long else "top",
                            "textColor": "rgba(255, 255, 255, 1)",
                            "fontSize": 12,
                            "bold": True,
                            "italic": True,
                            "extendLeft": False,
                            "extendRight": False,
                            "snapTo45Degrees": True,
                            "lastUpdateTime": int(datetime.datetime.now().timestamp()),
                            "fixedSize": True,
                            "symbolStateVersion": 2,
                            "zOrderVersion": 2,
                            "visible": True,
                            "frozen": False,
                            "symbol": symbol,
                            "unitId": None,
                            "title": "",
                            "text": text,
                            "interval": TradingViewTimeFrame.TF_1M.value
                        },
                        "points": [
                            {"time_t": point_one['time_t'], "offset": 0, "price": point_one['price']},
                            {"time_t": point_two['time_t'], "offset": 0, "price": point_two['price']}
                        ],
                        "zorder": -2500,
                        "ownerSource": self.parameters.owner_source,
                        "linkKey": link_key
                    },
                    "symbol": symbol,
                    "unitId": None
                }
            },
            "drawing_groups": {
                drawing_group['id']: drawing_group
            },
            "clientId": self.parameters.client_id
        })

        url = edit_chart_url.format(self.parameters.layout_id, self.parameters.chart_id, self.parameters.jwt)
        return requests.put(url, body, headers=self.create_headers(symbol))

    def draw_arrow(
            self,
            point_one,
            point_two,
            color: str,
            drawing_group: Dict,
            text: str = '',
            symbol='BINANCE:BTCUSDTPERP'
    ):
        link_key = self.trading_view_id_generator.create_link_key()
        source_id = self.trading_view_id_generator.create_source_id()

        body = json.dumps({
            "sources": {
                source_id: {
                    "id": source_id,
                    "ownerSource": self.parameters.owner_source,
                    "groupId": drawing_group['id'],
                    "state": {
                        "type": "LineToolArrow",
                        "id": source_id,
                        "groupId": drawing_group['id'],
                        "state": {
                            "linecolor": color,
                            "linewidth": 1,
                            "linestyle": 0,
                            "extendLeft": False,
                            "extendRight": False,
                            "leftEnd": 0,
                            "rightEnd": 0,
                            "showLabel": True,
                            "horzLabelsAlign": "right",
                            "vertLabelsAlign": "bottom",
                            "textcolor": "rgba(255, 255, 255, 1)",
                            "fontsize": 14,
                            "bold": True,
                            "italic": True,
                            "alwaysShowStats": False,
                            "showMiddlePoint": False,
                            "showPriceLabels": False,
                            "showPriceRange": False,
                            "showBarsRange": False,
                            "showDateTimeRange": False,
                            "showDistance": False,
                            "showAngle": False,
                            "statsPosition": 2,
                            "symbolStateVersion": 2,
                            "zOrderVersion": 2,
                            "visible": True,
                            "frozen": False,
                            "symbol": symbol,
                            "unitId": None,
                            "title": "",
                            "text": text,
                            "interval": TradingViewTimeFrame.TF_1W.value
                        },
                        "points": [point_one, point_two],
                        "zorder": -1250,
                        "ownerSource": self.parameters.owner_source,
                        "linkKey": link_key
                    },
                    "symbol": symbol,
                    "unitId": None
                }
            },
            "drawing_groups": {
                drawing_group['id']: drawing_group
            },
            "clientId": self.parameters.client_id,
        })

        url = edit_chart_url.format(self.parameters.layout_id, self.parameters.chart_id, self.parameters.jwt)
        return requests.put(url, body, headers=self.create_headers(symbol))

    def create_headers(self, symbol):
        cookie = """cookiePrivacyPreferenceBannerProduction=notApplicable; cookiesSettings={"analytics":true,"advertising":true}; tv_ecuid=d03c0b1e-654a-4de4-9fa0-f232857df1d2; sessionid=; theme=dark; sessionid_sign=v1:RvCtacSUrlzyltPPEn2WBmrnPWlBQMnA3UqaOB/MwHk=; _ga=GA1.1.1780528908.1658800449; _sp_ses.cf1a=*; _sp_id.cf1a=636180c1-dc89-4561-86a8-b0c1e4076fe4.1658800440.1897.1699071926.1696754217.1498fc4a-c671-49de-8fc7-95d98cb0bf47; _ga_YVVRYGL0E0=GS1.1.1699071914.524.1.1699071941.33.0.0"""
        cookie = cookie.replace("sessionid=", "sessionid=" + self.parameters.get_session_id())
        return {
            "Cookie": cookie,
            "Content-Type": "application/json",
            'Origin': 'https://www.tradingview.com',
            'Referer': 'https://www.tradingview.com/',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': 'Linux',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }
