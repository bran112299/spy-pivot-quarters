import re

from infrastructure.tradingview.drawing.trading_view_id_generator import TradingViewIdGenerator
from infrastructure.tradingview.time_frames.trading_view_time_frame import TradingViewTimeFrame


class DrawingGroupInMemoryRepository:
    def __init__(self, id_generator: TradingViewIdGenerator):
        self.id_generator = id_generator
        self.groups = {}

    def get_drawing_group(self, symbol: str, prefix: str, trading_view_time_frame: TradingViewTimeFrame = None):
        if symbol not in self.groups:
            self.groups[symbol] = {}

        if trading_view_time_frame is not None:
            name = "{} {}".format(prefix, trading_view_time_frame.get_description())
        else:
            name = prefix
        if name not in self.groups[symbol]:
            self.groups[symbol][name] = {
                "id": self.id_generator.create_source_id(),
                "name": name,
                "symbol": symbol,
                "currencyId": None,
                "unitId": None
            }
        return self.groups[symbol][name]

    def get_visibility_timeframes(self, trading_view_time_frame: TradingViewTimeFrame, shift):
        # Truly the ugliest solution ive ever come up with
        def get_timeframe(tf_str):
            tf = TradingViewTimeFrame.get_description(TradingViewTimeFrame.from_string(tf_str))
            t = re.search("\d+", tf).group() if re.search("\d+", tf) else 1
            i = None
            tf_char = tf[-1]

            if tf_char == '.':
                i = 'minutes'
            elif tf_char == 'h':
                i = 'hours'
            elif tf_char == 'y':
                if tf == 'daily':
                    i = 'days'
                elif tf == 'weekly':
                    i = 'weeks'
                elif tf == 'monthly':
                    i = 'months'

            return int(t), i

        visibility_dict = {}
        tv_tf = [tf.value for tf in TradingViewTimeFrame]

        if shift == 0:
            return visibility_dict

        curr_tf = tv_tf.index(trading_view_time_frame.value)

        visibility_dict['seconds'] = False
        visibility_dict['minutes'] = False
        visibility_dict['hours'] = False
        visibility_dict['days'] = False
        visibility_dict['weeks'] = False
        visibility_dict['months'] = False

        min = curr_tf - shift if curr_tf - shift > 0 else 0
        max = curr_tf + shift + 1 if curr_tf + shift + 1 < len(tv_tf) else len(tv_tf) + 1

        # print(get_timeframe(tv_tf[curr_tf]), curr_tf,  ":")

        init_t, init_i = get_timeframe(tv_tf[min])
        visibility_dict[init_i + "From"] = init_t
        del (visibility_dict[init_i])

        for tf in tv_tf[min + 1:max]:
            t, i = get_timeframe(tf)

            if i == init_i:
                # print(t, i, 'if')
                visibility_dict[init_i + "To"] = t
            else:
                # print(t, i, 'else')
                init_i = i
                visibility_dict[init_i + "From"] = t
                del (visibility_dict[init_i])

        max = len(tv_tf) - 1 if max > len(tv_tf) else max - 1  # makes me wanna puke
        max_t, max_i = get_timeframe(tv_tf[max])
        visibility_dict[max_i + "To"] = max_t
        # print(max_t, max_i)
        # print(visibility_dict, "\n")

        return visibility_dict
