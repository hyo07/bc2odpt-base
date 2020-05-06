import json
from time import time
import hashlib
import binascii
from datetime import datetime
import random

from setting import *


class Block:
    def __init__(self, transactions, previous_block_hash, block_num, address, sc_self=None):
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
        self.address = address
        self.sc_self = sc_self
        self.lose_flag = False

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
            # "merkle_root": self._gene_merkle(json.dumps(self.transactions)),
            "nTx": len(self.transactions),
            'previous_block': self.previous_block,
            'address': self.address,
            'difficulty': DIFFICULTY,
        }

        if self.transactions:
            d["merkle_root"] = self._gene_merkle(json.dumps(self.transactions))
        else:
            d["merkle_root"] = ""

        if self.lose_flag:
            return {}

        if include_nonce:
            d['nonce'] = self.nonce
            d["transactions"] = json.dumps(self.transactions)

        return d

    def _compute_nonce_for_pow(self, message, difficulty=DIFFICULTY):
        # difficultyの数字を増やせば増やすほど、末尾で揃えなければならない桁数が増える。
        i = 0
        suffix = '0' * difficulty
        count = 0
        while True:

            if self.sc_self:
                if int(self.b_num) <= int(self.sc_self.bm.chain[-1]["block_number"]):
                    self.lose_flag = True
                    return 0

            count += 1
            if count % 200000 == 0:
                print("Mining!")
                if self.sc_self:
                    if count % 2000000 == 0:
                        print(self.sc_self.bm.chain)
                    print("latest_block_num:", self.b_num)
                    print("timestamp:", self.timestamp)
                    print()

            nonce = str(i)
            digest = binascii.hexlify(self._get_double_sha256((message + nonce).encode('utf-8'))).decode('ascii')
            if digest.endswith(suffix):
                return nonce
            # i += 1
            i += random.randint(1, 10)

    def _get_double_sha256(self, message):
        return hashlib.sha256(hashlib.sha256(message).digest()).digest()

    def _gene_merkle(self, tx_list: str):
        tx_list = [binascii.hexlify(hashlib.sha256(json.dumps(tx).encode('utf-8')).digest()).decode('ascii') for tx in
                   json.loads(tx_list)]

        if not tx_list:
            return binascii.hexlify(hashlib.sha256(json.dumps(tx_list).encode('utf-8')).digest()).decode('ascii')

        while len(tx_list) > 1:
            latest_merkle_list = []

            if len(tx_list) % 2 == 1:
                tx_list.append(tx_list[-1])

            for i in range(0, len(tx_list), 2):
                one_hash = binascii.hexlify(hashlib.sha256(tx_list[i].encode('utf-8')).digest()).decode('ascii')
                two_hash = binascii.hexlify(hashlib.sha256(tx_list[i + 1].encode('utf-8')).digest()).decode('ascii')
                new_hash = binascii.hexlify(hashlib.sha256((one_hash + two_hash).encode('utf-8')).digest()).decode(
                    'ascii')
                latest_merkle_list.append(new_hash)

            tx_list = latest_merkle_list

        return tx_list[0]


class GenesisBlock(Block):
    """
    前方にブロックを持たないブロックチェーンの始原となるブロック。
    transaction にセットしているのは「{"message":"this_is_simple_bitcoin_genesis_block"}」をSHA256でハッシュしたもの。深い意味はない
    """

    def __init__(self):
        super().__init__(transactions='AD9B477B42B22CDF18B1335603D07378ACE83561D8398FBFC8DE94196C65D806',
                         previous_block_hash=None, block_num="0", address=None)

    def to_dict(self, include_nonce=True):
        d = {
            'block_number': "0",
            'transactions': self.transactions,
            'genesis_block': True,
            'timestamp': self.timestamp,
        }
        if include_nonce:
            d['nonce'] = self.nonce
        return d
