import json
from time import time
import hashlib
import binascii
from datetime import datetime
import random

from setting import *


class Block:
    def __init__(self, transactions, previous_block_hash, block_num):
        """
        Args:
            transaction: ブロック内にセットされるトランザクション
            previous_block_hash: 直前のブロックのハッシュ値
        """
        snap_tr = json.dumps(transactions)  # PoW計算中に値が変わるのでブロック計算開始時の値を退避させておく

        self.timestamp = time()
        self.transactions = json.loads(snap_tr)
        self.previous_block = previous_block_hash
        self.b_num = block_num
        # self.address = address

        current = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        if DEBUG:
            print(current)

        json_block = json.dumps(self.to_dict(include_nonce=False), sort_keys=True)
        if DEBUG:
            print('json_block :', json_block)
        self.nonce = self._compute_nonce_for_pow(json_block)

        current2 = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        if DEBUG:
            print(current2)

    def to_dict(self, include_nonce=True):
        d = {
            'block_number': str(self.b_num),
            'timestamp': self.timestamp,
            'transactions': list(map(json.dumps, self.transactions)),
            'previous_block': self.previous_block,
            # 'address': self.address,
        }

        if include_nonce:
            d['nonce'] = self.nonce
        return d

    def _compute_nonce_for_pow(self, message, difficulty=DIFFICULTY):
        # difficultyの数字を増やせば増やすほど、末尾で揃えなければならない桁数が増える。
        i = 0
        suffix = '0' * difficulty
        while True:
            nonce = str(i)
            digest = binascii.hexlify(self._get_double_sha256((message + nonce).encode('utf-8'))).decode('ascii')
            if digest.endswith(suffix):
                return nonce
            # i += 1
            i += random.randint(1, 10)

    def _get_double_sha256(self, message):
        return hashlib.sha256(hashlib.sha256(message).digest()).digest()


class GenesisBlock(Block):
    """
    前方にブロックを持たないブロックチェーンの始原となるブロック。
    transaction にセットしているのは「{"message":"this_is_simple_bitcoin_genesis_block"}」をSHA256でハッシュしたもの。深い意味はない
    """

    def __init__(self):
        super().__init__(transactions='AD9B477B42B22CDF18B1335603D07378ACE83561D8398FBFC8DE94196C65D806',
                         previous_block_hash=None, block_num="0")

    def to_dict(self, include_nonce=True):
        d = {
            'block_number': "0",
            'transactions': self.transactions,
            'genesis_block': True,
        }
        if include_nonce:
            d['nonce'] = self.nonce
        return d
