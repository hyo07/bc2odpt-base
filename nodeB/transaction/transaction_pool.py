import threading
import hashlib
import json
import binascii


class TransactionPool:

    def __init__(self):
        print('Initializing TransactionPool...')
        self.transactions = {}
        # self.hash_txs = set()
        # TODO
        self.hash_txs = dict()
        self.lock = threading.Lock()

    # tx poolに新規追加, txハッシュリストにも追加
    def check_duplicates_and_set_tx(self, transaction: list):
        with self.lock:
            # flag = False
            for tx in transaction:
                # hash_tx = binascii.hexlify(hashlib.sha256(json.dumps(tx).encode('utf-8')).digest()).decode('ascii')
                cl_addr = tx.get("client_address")
                hash_tx = self._hash_tx(tx)
                if not hash_tx in self.hash_txs:
                    # self.hash_txs.add(hash_tx)

                    # TODO
                    # setへの追加 -> dictへの追加 に変更
                    # self.hash_txs[hash_tx] = set()
                    self.hash_txs[hash_tx] = {"addrs": set(), "count": 0}

                    self.transactions[hash_tx] = tx
                    # flag = True

                # TODO
                # ハッシュtxセットに追加
                # self.hash_txs[hash_tx].add(cl_addr)
                self.hash_txs[hash_tx]["addrs"].add(cl_addr)

        # return flag

    # tx poolから削除
    def clear_my_transactions2(self, txs: dict):
        with self.lock:
            for tx in txs.keys():
                # # hash_tx = binascii.hexlify(hashlib.sha256(json.dumps(tx).encode('utf-8')).digest()).decode('ascii')
                # hash_tx = self._hash_tx(tx)
                hash_tx = tx
                try:
                    del self.transactions[hash_tx]
                except KeyError:
                    pass

    # txハッシュリストから削除
    def clear_my_hash_txs(self, txs: list):
        with self.lock:
            for tx in txs:
                # hash_tx = binascii.hexlify(hashlib.sha256(json.dumps(tx).encode('utf-8')).digest()).decode('ascii')
                hash_tx = self._hash_tx(tx)
                try:
                    # self.hash_txs.remove(hash_tx)

                    # TODO
                    # setから削除 -> dictのkeyから削除 にする
                    del self.hash_txs[hash_tx]

                # except ValueError:
                except KeyError:
                    pass

    # tx pool取得
    def get_stored_transactions2(self):
        with self.lock:
            return list(self.transactions.values())

    def get_stored_transactions3(self):
        with self.lock:
            # メモリアドレスを変更した値を返したい（参照渡ししたくない）
            return dict(self.transactions)

    # txハッシュリスト取得
    def get_txs_hash_len(self):
        with self.lock:
            return len(self.hash_txs)

    def get_txs_hash(self):
        with self.lock:
            # メモリアドレスを変更した値を返したい（参照渡ししたくない）
            return dict(self.hash_txs)

    # 分岐解消時、上書きされたブロックに含まれるtxがまだpoolに残っていないか などの辻褄を合わせる
    def justification_conflict(self, blocks: list):
        with self.lock:
            for block in blocks:
                for tx in json.loads(block["transactions"]):
                    cl_addr = tx.get("client_address")
                    try:
                        # hash_tx = binascii.hexlify(hashlib.sha256(json.dumps(tx).encode('utf-8')).digest()).decode(
                        #     'ascii')
                        hash_tx = self._hash_tx(tx)
                    except json.decoder.JSONDecodeError:
                        pass
                    try:
                        # tx poolに存在する場合,削除する 存在する場合txハッシュリストにも存在すると判断できる
                        del self.transactions[hash_tx]
                    except KeyError:
                        # tx poolに無く,txハッシュリストにも存在しない場合がある. その場合は追加する
                        if not hash_tx in self.hash_txs:
                            # self.hash_txs.append(hash_tx)
                            # self.hash_txs.add(hash_tx)

                            # TODO
                            # setへの追加 -> dictへの追加 に変更
                            # self.hash_txs[hash_tx] = set()
                            self.hash_txs[hash_tx] = {"addrs": set(), "count": 0}
                        # TODO
                        # ハッシュtxセットに追加
                        self.hash_txs[hash_tx]["addrs"].add(cl_addr)

    # スルーされた回数を進める
    def add_through_count(self, exclusion_txs: list):
        with self.lock:
            for ex_tx in exclusion_txs:
                self.hash_txs[ex_tx]["count"] += 1

    def _hash_tx(self, tx):
        # cl_addr = tx.pop("client_address")
        try:
            del tx["client_address"]
        except KeyError:
            pass
        hash_tx = binascii.hexlify(hashlib.sha256(json.dumps(tx).encode('utf-8')).digest()).decode('ascii')
        # tx["client_address"] = cl_addr
        return hash_tx

    # 最大多数の原理でブロックが更新されたとき、旧ブロックに存在し深ブロックに存在しないtxをtxpoolに戻す
    def increment_tx(self, old_block, new_block):
        old_tx = json.loads(old_block["transactions"])
        old_addrs = json.loads(old_block["addrs"])
        new_addrs = new_block["addrs"]
        survive_dict = dict()
        for hash_tx, raw_tx in zip(old_addrs.keys(), old_tx):
            if not hash_tx in new_addrs:
                survive_dict[hash_tx] = raw_tx
        with self.lock:
            self.transactions.update(survive_dict)
