import random


class TradingViewIdGenerator:
    def create_client_id(self):
        # owqvJMUt1x6Z
        return ''.join([str(random.randint(0, 999)).zfill(3) for _ in range(4)])

    def create_source_id(self):
        # czzqct
        # gU7QR6
        return ''.join([str(random.randint(0, 999)).zfill(3) for _ in range(2)])

    def create_link_key(self):
        # JVLxpqeqt6Dn
        return ''.join([str(random.randint(0, 999)).zfill(3) for _ in range(4)])