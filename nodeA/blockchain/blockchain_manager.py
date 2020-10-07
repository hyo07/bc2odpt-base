import json
import hashlib
import binascii
import copy
import threading

from setting import *

from p2p.connection_manager import LDB_P, PARAM_P, ZIP_P
from libs import main_level, level_param

FORK_LEN = 6


class BlockchainManager:

    def __init__(self, genesis_block=None):
        print('Initializing BlockchainManager...')
        self.chain = []
        self.lock = threading.Lock()
        if genesis_block:
            self.__set_my_genesis_block(genesis_block)

    def __set_my_genesis_block(self, block):
        self.genesis_block = block
        self.chain.append(block)

    def set_reconnect_block(self, block):
        with self.lock:
            self.chain.append(block)

    def set_new_block(self, block, prev_hash):
        with self.lock:
            if int(self.chain[-1]["block_number"]) < int(block["block_number"]):
                if self.is_valid_block(prev_hash, block):
                    self.chain.append(block)
                    return True
            # elif (int(self.chain[-1]["block_number"]) == int(block["block_number"])) and (
            #         self.chain[-1]["total_majority"] < block["total_majority"]):
            #     if self.is_valid_block_booby(block):
            #         deleted_block = self.chain.pop(-1)
            #         # TODO 本当は既存ブロックのtxと置き換わる新規ブロックの差分をtx pool に適用させたい
            #         self.chain.append(block)
            #         return True
            else:
                return False
        return False

    # def replace_latest_block(self, block):
    #     with self.lock:
    #         if self.chain[-1]["total_majority"] < block["total_majority"] and int(
    #                 self.chain[-1]["block_number"]) == int(block["block_number"]):
    #             deleted_blcok = self.chain.pop(-1)
    #             self.chain.append(block)
    #             return deleted_blcok
    #         else:
    #             return None

    def renew_my_blockchain(self, blockchain):
        # ブロックチェーン自体を更新し、それによって変更されるはずの最新のprev_block_hashを計算して返却する
        with self.lock:
            if self.is_valid_chain(blockchain):
                self.chain = blockchain

                # if len(self.chain) >= SAVE_BORDER:
                #     saved_bc = self.chain[:SAVE_BORDER_HALF]
                #     self.chain = self.chain[SAVE_BORDER_HALF:]
                #     main_level.add_db(ldb_p=LDB_P, param_p=PARAM_P, zip_p=ZIP_P, vals=saved_bc)
                #     print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                #     print("保存しました")
                #     print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")

                latest_block = self.chain[-1]
                return self.get_hash(latest_block)
            else:
                if DEBUG:
                    print('invalid chain cannot be set...')
                return None

    def renew_my_blockchain2(self, new_blockchain, len_diff: int):
        # ブロックチェーン自体を更新し、それによって変更されるはずの最新のprev_block_hashを計算して返却する
        with self.lock:
            if self.is_valid_chain(new_blockchain):
                if len_diff >= FORK_LEN:
                    self.chain = new_blockchain
                else:
                    merge_len = FORK_LEN - len_diff
                    self.chain = self.chain[:(-1 * merge_len)] + new_blockchain[(-1 * FORK_LEN):]

                # if len(self.chain) >= SAVE_BORDER:
                #     saved_bc = self.chain[:SAVE_BORDER_HALF]
                #     self.chain = self.chain[SAVE_BORDER_HALF:]
                #     main_level.add_db(ldb_p=LDB_P, param_p=PARAM_P, zip_p=ZIP_P, vals=saved_bc)
                #     print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                #     print("保存しました")
                #     print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")

                latest_block = self.chain[-1]
                return self.get_hash(latest_block)
            else:
                if DEBUG:
                    print('invalid chain cannot be set...')
                return None

    def get_my_blockchain(self):
        if len(self.chain) > 1:
            return self.chain
        else:
            return None

    def get_my_chain_length(self):
        return len(self.chain)

    def get_transactions_from_orphan_blocks(self, orphan_blocks):
        # if "genesis_block" in self.chain[0]:
        #     current_index = 1
        # else:
        current_index = 0

        new_transactions = []

        while current_index < len(orphan_blocks):
            block = orphan_blocks[current_index]
            transactions = block['transactions']
            target = self.remove_useless_transaction(transactions)
            for t in target:
                new_transactions.append(t)

        return new_transactions

    def remove_useless_transaction(self, transaction_pool):
        """remove_useless_transaction
        与えられたTransactionのリストの中で既に自分が管理するブロックチェーン内に含まれたTransactionがある場合、それを削除したものを返却する
            param :
                transaction_pool: 検証したいTransactionのリスト。TransactionPoolに格納されているデータを想定

            return :
                整理されたTransactionのリスト。与えられたリストがNoneの場合にはNoneを返す
        """

        if len(transaction_pool) != 0:
            if "genesis_block" in self.chain[0]:
                current_index = 1
            else:
                current_index = 0

            while current_index < len(self.chain):
                block = self.chain[current_index]
                transactions = block['transactions']
                for t in transactions:
                    for t2 in transaction_pool:
                        # ブロックに格納するタイミングで json.dumps してるので普通に比較すると死ぬ
                        if t == json.dumps(t2):
                            if DEBUG:
                                print('already exist in my blockchain :', t2)
                            transaction_pool.remove(t2)

                current_index += 1
            return transaction_pool
        else:
            # print('no transaction to be removed...')
            return []

    def resolve_conflicts(self, chain):
        # 自分のブロックチェーンと比較して、長い方を有効とする。有効性検証自体はrenew_my_blockchainで実施
        mychain_len = len(self.chain)
        new_chain_len = len(chain)

        mychain_num = int(self.chain[-1]["block_number"])
        new_chain_num = int(chain[-1]["block_number"])

        pool_4_orphan_blocks = copy.deepcopy(self.chain)
        has_orphan = False

        # 自分のチェーンの中でだけ処理済みとなっているTransactionを救出する。現在のチェーンに含まれていない
        # ブロックを全て取り出す。時系列を考えての有効無効判定などはしないかなり簡易な処理。

        # if (((new_chain_len > mychain_len) and (new_chain_num > mychain_num)) or (
        #         (int(self.chain[-1]["block_number"]) == int(chain[-1]["block_number"])) and (
        #         self.chain[-1]["total_majority"] < chain[-1]["total_majority"]))) and (
        #         (int(self.chain[0]["block_number"]) == int(chain[0]["block_number"])) or (
        #         self.chain[0]["block_number"] == "0") or (len(self.chain) < SAVE_BORDER_HALF)):

        if ((new_chain_len > mychain_len) and (new_chain_num > mychain_num)) and (
                (int(self.chain[0]["block_number"]) == int(chain[0]["block_number"])) or (
                self.chain[0]["block_number"] == "0") or (len(self.chain) < SAVE_BORDER_HALF)):

            result = self.renew_my_blockchain(chain)
            # result = self.renew_my_blockchain2(chain, new_chain_len - mychain_len)
            if DEBUG:
                print(result)
            if result is not None:
                return result, pool_4_orphan_blocks
            else:
                return None, []
        else:
            print('invalid chain cannot be set...')
            return None, []

    def is_valid_block(self, prev_block_hash, block):
        # ブロック単体の正当性を検証する
        block_4_pow = copy.deepcopy(block)
        nonce = block_4_pow['nonce']
        del block_4_pow['nonce']
        del block_4_pow['transactions']
        # del block_4_pow['addrs']
        if DEBUG:
            print(block_4_pow)

        message = json.dumps(block_4_pow, sort_keys=True)
        # print("message", message)
        nonce = str(nonce)

        if block['previous_block'] != prev_block_hash:
            if DEBUG:
                print('Invalid block (bad previous_block)')
                print(block['previous_block'])
                print(prev_block_hash)
            return False
        else:
            digest = binascii.hexlify(self._get_double_sha256((message + nonce).encode('utf-8'))).decode('ascii')
            # if digest.endswith(suffix):
            #     print('OK, this seems valid block')
            #     return True
            if int(digest, 16) <= int(block_4_pow["target"], 16):
                print('OK, this seems valid block')
                return True
            else:
                if DEBUG:
                    print('Invalid block (bad nonce)')
                    print('nonce :', nonce)
                    print('digest :', digest)
                    # print('suffix', suffix)
                return False

    def is_valid_block_booby(self, block):
        # ブロック単体の正当性を検証する
        block_4_pow = copy.deepcopy(block)
        nonce = block_4_pow['nonce']
        del block_4_pow['nonce']
        del block_4_pow['transactions']
        # del block_4_pow['addrs']
        if DEBUG:
            print(block_4_pow)

        message = json.dumps(block_4_pow, sort_keys=True)
        # print("message", message)
        nonce = str(nonce)

        prev_block_hash = self.get_hash(self.chain[-2])

        if block['previous_block'] != prev_block_hash:
            if DEBUG:
                print('Invalid block (bad previous_block)')
                print(block['previous_block'])
                print(prev_block_hash)
            return False
        else:
            digest = binascii.hexlify(self._get_double_sha256((message + nonce).encode('utf-8'))).decode('ascii')
            # if digest.endswith(suffix):
            #     print('OK, this seems valid block')
            #     return True
            if int(digest, 16) <= int(block_4_pow["target"], 16):
                print('OK, this seems valid block')
                return True
            else:
                if DEBUG:
                    print('Invalid block (bad nonce)')
                    print('nonce :', nonce)
                    print('digest :', digest)
                    # print('suffix', suffix)
                return False

    def is_valid_chain(self, chain):
        # ブロック全体の正当性を検証する
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if self.is_valid_block(self.get_hash(last_block), block) is not True:
                return False

            last_block = chain[current_index]
            current_index += 1

        return True

    def _get_double_sha256(self, message):
        return hashlib.sha256(hashlib.sha256(message).digest()).digest()

    def get_hash(self, block):
        """
        正当性確認に使うためブロックのハッシュ値を取る
            param
                block: Block
        """
        if DEBUG:
            print('BlockchainManager: get_hash was called!')
        block_string = json.dumps(block, sort_keys=True)
        # print("BlockchainManager: block_string", block_string)
        return binascii.hexlify(self._get_double_sha256((block_string).encode('utf-8'))).decode('ascii')

    # TODO こっちのが良いのか案
    # def get_hash(self, block):
    #     """
    #     正当性確認に使うためブロックのハッシュ値を取る
    #         param
    #             block: Block
    #     """
    #     copy_block = copy.deepcopy(block)
    #     del copy_block['nonce']
    #     del copy_block['transactions']
    #     del copy_block['addrs']
    #
    #     if DEBUG:
    #         print('BlockchainManager: get_hash was called!')
    #     block_string = json.dumps(copy_block, sort_keys=True)
    #     # print("BlockchainManager: block_string", block_string)
    #     return binascii.hexlify(self._get_double_sha256((block_string).encode('utf-8'))).decode('ascii')

    def save_block_2_db(self):
        with self.lock:
            # if self.is_bb_running:
            #     self.flag_stop_block_build = True
            saved_bc = []

            if len(self.chain) >= SAVE_BORDER:
                saved_bc = self.chain[:SAVE_BORDER_HALF]
                self.chain = self.chain[SAVE_BORDER_HALF:]
                main_level.add_db(ldb_p=LDB_P, param_p=PARAM_P, zip_p=ZIP_P, vals=saved_bc)
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                print("保存しました")
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")

            # self.flag_stop_block_build = False
        return saved_bc
