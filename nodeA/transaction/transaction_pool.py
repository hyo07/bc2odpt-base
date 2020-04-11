import threading
import hashlib
import json
import binascii


class TransactionPool:

    def __init__(self):
        print('Initializing TransactionPool...')
        # self.transactions = []
        self.transactions = {}
        self.hash_txs = []
        self.lock = threading.Lock()

    def set_new_transaction(self, transaction: list):
        with self.lock:
            print('set_new_transaction is called', transaction)
            # self.transactions.append(transaction)
            self.transactions += transaction

    def check_duplicates_and_set_tx(self, transaction: list):
        with self.lock:
            flag = False
            for tx in transaction:
                hash_tx = binascii.hexlify(hashlib.sha256(json.dumps(tx).encode('utf-8')).digest()).decode('ascii')
                if not hash_tx in self.hash_txs:
                    self.hash_txs.append(hash_tx)
                    # self.transactions.append(tx)
                    self.transactions[hash_tx] = tx
                    flag = True
        return flag

    def check_duplicates(self, transaction: list):
        with self.lock:
            new_txs = []
            for tx in transaction:
                hash_tx = binascii.hexlify(hashlib.sha256(json.dumps(tx).encode('utf-8')).digest()).decode('ascii')
                if not hash_tx in self.hash_txs:
                    self.hash_txs.append(hash_tx)
                    new_txs.append(tx)
        return new_txs

    def clear_my_transactions(self, index):
        with self.lock:
            if index <= len(self.transactions):
                new_transactions = self.transactions
                del new_transactions[0:index]
                print('transaction is now refreshed ... ', new_transactions)
                self.transactions = new_transactions

    def clear_my_transactions2(self, txs: list):
        with self.lock:
            for tx in txs:
                hash_tx = binascii.hexlify(hashlib.sha256(json.dumps(tx).encode('utf-8')).digest()).decode('ascii')
                try:
                    del self.transactions[hash_tx]
                except KeyError:
                    pass

    def clear_my_hash_txs(self, txs: list):
        with self.lock:
            for tx in txs:
                hash_tx = binascii.hexlify(hashlib.sha256(json.dumps(tx).encode('utf-8')).digest()).decode('ascii')
                try:
                    self.hash_txs.remove(hash_tx)
                except ValueError:
                    pass

    def get_stored_transactions(self):
        if len(self.transactions) > 0:
            return self.transactions
        else:
            print("Currently, it seems transaction pool is empty...")
            return []

    def get_stored_transactions2(self):
        return list(self.transactions.values())

    def get_txs_hash_len(self):
        return len(self.hash_txs)

    def renew_my_transactions(self, transactions):
        with self.lock:
            print('transaction pool will be renewed to ...', transactions)
            self.transactions = transactions
