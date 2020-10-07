import json
from time import time
import hashlib
import binascii
from datetime import datetime
import random
from copy import deepcopy

from setting import *


class Block:
    def __init__(self, transactions, previous_block_hash, block_num, address, hash_txs, sc_self=None):
        """
        Args:
            transaction: ブロック内にセットされるトランザクション
            previous_block_hash: 直前のブロックのハッシュ値
        """

        self.timestamp = time()
        self.transactions = transactions
        self.previous_block = deepcopy(previous_block_hash)
        self.b_num = block_num
        self.address = address
        self.sc_self = sc_self
        self.lose_flag = False
        self.exclusion_tx = []
        self.max_addrs = 0
        # self.include_hashs = self._included_hash_txs(hash_txs)
        # self.over_half = int(self.max_addrs / 2 + 1)
        # if self.over_half < 2:
        #     self.over_half = 2
        # self.total_clients = self._sum_all_client(self.include_hashs, self.over_half)
        self.target = self.adjust_target()
        self.test = None

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
        target_16 = format(int(self.target), "x")
        if len(target_16) < 64:
            target_16 = ("0" * (64 - len(target_16))) + target_16
        self.test = target_16
        d = {
            'block_number': str(self.b_num),
            'timestamp': self.timestamp,
            "nTx": len(self.transactions),
            'previous_block': self.previous_block,
            'address': self.address,
            # 'target': TARGET,
            "target": target_16,
            # 'total_majority': self.total_clients,
            # "over_half": self.over_half,
        }

        if self.lose_flag:
            return {}

        if self.transactions:
            d["merkle_root"] = self._gene_merkle(json.dumps(self.transactions))
        else:
            d["merkle_root"] = ""

        if include_nonce:
            d['nonce'] = self.nonce
            d["transactions"] = json.dumps(list(self.transactions.values()))
            # d['addrs'] = json.dumps(self.include_hashs)

        return d

    def get_exclusion_tx(self):
        return self.exclusion_tx

    # def _compute_nonce_for_pow(self, message, difficulty=DIFFICULTY):
    #     # difficultyの数字を増やせば増やすほど、末尾で揃えなければならない桁数が増える。
    #     i = 0
    #     suffix = '0' * difficulty
    #     count = 0
    #     while True:
    #
    #         # if self.sc_self and self.sc_self.bm.chain:
    #         #     if len(self.sc_self.bm.chain) > 1:
    #         #         if int(self.b_num) <= int(self.sc_self.bm.chain[-1]["block_number"]):
    #         #             self.lose_flag = True
    #         #             return 0
    #
    #         if self.sc_self and self.sc_self.bm.chain:
    #             if len(self.sc_self.bm.chain) > 1:
    #                 if (int(self.b_num) < int(self.sc_self.bm.chain[-1]["block_number"])) or (
    #                         (int(self.b_num) == int(self.sc_self.bm.chain[-1]["block_number"])) and (
    #                         self.total_clients <= self.sc_self.bm.chain[-1]["total_majority"])) or (
    #                         (self.previous_block is not self.sc_self.prev_block_hash) and (
    #                         (int(self.b_num) - int(self.sc_self.bm.chain[-1]["block_number"])) == 1)):
    #                     self.lose_flag = True
    #                     return 0
    #
    #         count += 1
    #         if count % 200000 == 0:
    #             count = 0
    #             print("Mining!")
    #             if self.sc_self:
    #                 # if count % 2000000 == 0:
    #                 #     print(self.sc_self.bm.chain)
    #                 print("latest_block_num:", self.b_num)
    #                 print("timestamp:", self.timestamp)
    #                 print()
    #
    #         nonce = str(i)
    #         digest = binascii.hexlify(self._get_double_sha256((message + nonce).encode('utf-8'))).decode('ascii')
    #         if digest.endswith(suffix):
    #             return nonce
    #         i += 1
    #         # i += random.randint(1, 10)

    def _compute_nonce_for_pow(self, message):
        i = 0
        while True:
            if self.sc_self and self.sc_self.bm.chain:
                if len(self.sc_self.bm.chain) > 1:
                    # if (int(self.b_num) < int(self.sc_self.bm.chain[-1]["block_number"])) or (
                    #         (int(self.b_num) == int(self.sc_self.bm.chain[-1]["block_number"])) and (
                    #         self.total_clients <= self.sc_self.bm.chain[-1]["total_majority"])) or (
                    #         (self.previous_block is not self.sc_self.prev_block_hash) and (
                    #         (int(self.b_num) - int(self.sc_self.bm.chain[-1]["block_number"])) == 1)):
                    #     self.lose_flag = True
                    #     return 0
                    if (int(self.b_num) <= int(self.sc_self.bm.chain[-1]["block_number"])) or (
                            (self.previous_block is not self.sc_self.prev_block_hash) and (
                            (int(self.b_num) - int(self.sc_self.bm.chain[-1]["block_number"])) == 1)):
                        self.lose_flag = True
                        return 0

            if i % 200000 == 0:
                print("Mining!")
                print(f"target: {self.test}")
                if self.sc_self:
                    # if count % 2000000 == 0:
                    #     print(self.sc_self.bm.chain)
                    print("latest_block_num:", self.b_num)
                    print("timestamp:", self.timestamp)
                    print()

            nonce = str(i)
            digest = binascii.hexlify(self._get_double_sha256((message + nonce).encode('utf-8'))).decode('ascii')
            if int(digest, 16) <= self.target:
                return nonce
            i += 1
            # i += random.randint(1, 10)

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

    # def _included_hash_txs(self, hash_txs: dict):
    #     if not hash_txs:
    #         return {}
    #     have_hash_txs = dict()
    #     addr_set = set()
    #     # for tx in self.transactions:
    #     #     hash_tx = binascii.hexlify(hashlib.sha256(json.dumps(tx).encode('utf-8')).digest()).decode('ascii')
    #     #     have_hash_txs[hash_tx] = list(hash_txs[hash_tx])
    #
    #     tx_keys = self.transactions.keys()
    #     for tx_hash in tx_keys:
    #         # TODO 此処でなぜかKey Error出てしまう。根本的な原因不明。とりあえずやりたくないけどtryでスルーする
    #         try:
    #             # client_addrs = list(hash_txs[tx_hash]["addrs"])
    #             client_addrs = list(hash_txs[tx_hash]["addrs"])
    #             exclusion_count = hash_txs[tx_hash]["count"]
    #             # have_hash_txs[tx_hash] = client_addrs
    #             for ad in client_addrs:
    #                 addr_set.add(ad)
    #             have_hash_txs[tx_hash] = {"addrs": client_addrs, "count": exclusion_count}
    #         except KeyError:
    #             pass
    #     self.max_addrs = len(addr_set)
    #     return have_hash_txs

    # def _sum_all_client(self, hashs: dict, n: int):
    #     if not hashs:
    #         return 0
    #     total = 0
    #     del_list = list()
    #     for k, v in hashs.items():
    #         if len(v["addrs"]) < n:
    #             del_list.append(k)
    #             if v["count"] < THROUGH:
    #                 self.exclusion_tx.append(k)
    #         else:
    #             total += len(v["addrs"])
    #
    #     for del_hash in del_list:
    #         try:
    #             del self.transactions[del_hash]
    #             del self.include_hashs[del_hash]
    #         except KeyError:
    #             pass
    #
    #     return total

    def adjust_target(self):
        if (TARGET_ADUJST is False) or (not (self.sc_self and self.sc_self.bm.chain)) or (
                len(self.sc_self.bm.chain) < SAVE_BORDER_HALF):
            default_target = ('0' * TARGET) + ((64 - TARGET) * "f")
            return int(default_target, 16)
        else:
            chain = list(self.sc_self.bm.chain)
            chain = chain[-1 * SAVE_BORDER_HALF:]
            start_ts = chain[0]["timestamp"]
            total_ts = self.timestamp - start_ts

            total_probability = 0
            sha256_max = int("f" * 64, 16)
            for block in chain:
                w_s = int(block["target"], 16) / sha256_max
                total_probability += 1 / w_s
            w_t1 = (total_ts / 60) / (POW_TIME * total_probability)
            return int(w_t1 * sha256_max)


class GenesisBlock(Block):
    """
    前方にブロックを持たないブロックチェーンの始原となるブロック。
    transaction にセットしているのは「{"message":"this_is_simple_bitcoin_genesis_block"}」をSHA256でハッシュしたもの。深い意味はない
    """

    def __init__(self):
        super().__init__(transactions='AD9B477B42B22CDF18B1335603D07378ACE83561D8398FBFC8DE94196C65D806',
                         previous_block_hash=None, block_num="0", address=None, hash_txs={})

    def to_dict(self, include_nonce=True):
        d = {
            'block_number': "0",
            'transactions': self.transactions,
            'genesis_block': True,
            'timestamp': self.timestamp,
            "target": ('0' * TARGET) + ((64 - TARGET) * "f"),
        }
        if include_nonce:
            d['nonce'] = self.nonce
        return d
