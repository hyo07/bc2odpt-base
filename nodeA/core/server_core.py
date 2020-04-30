import socket
import threading
import json
import pickle

from libs import main_level, level_param

from blockchain.blockchain_manager import BlockchainManager
from blockchain.block_builder import BlockBuilder
from transaction.transaction_pool import TransactionPool
from p2p.connection_manager import ConnectionManager
from p2p.my_protocol_message_handler import MyProtocolMessageHandler
from p2p.message_manager import (
    MSG_NEW_TRANSACTION,
    MSG_NEW_BLOCK,
    MSG_REQUEST_FULL_CHAIN,
    RSP_FULL_CHAIN,
    MSG_ENHANCED,
    SHARE_DB3,
)

from p2p.connection_manager import LDB_P, PARAM_P, ZIP_P
from setting import *

STATE_INIT = 0
STATE_STANDBY = 1
STATE_CONNECTED_TO_NETWORK = 2
STATE_SHUTTING_DOWN = 3

# TransactionPoolの確認頻度
# 動作チェック用に数字小さくしてるけど、600(10分)くらいはあって良さそ
CHECK_INTERVAL = 0

DEBUG = True


class ServerCore(object):

    def __init__(self, my_port=50082, core_node_host=None, core_node_port=None):
        self.server_state = STATE_INIT
        print('Initializing server...')
        self.my_ip = self.__get_myip()
        print('Server IP address is set to ... ', self.my_ip)
        self.my_port = my_port
        self.cm = ConnectionManager(self.my_ip, self.my_port, self.__handle_message, self)
        self.mpmh = MyProtocolMessageHandler()
        self.core_node_host = core_node_host
        self.core_node_port = core_node_port
        self.bb = BlockBuilder()
        self.flag_stop_block_build = True
        self.is_bb_running = False
        my_genesis_block = self.bb.generate_genesis_block()
        self.bm = BlockchainManager(my_genesis_block.to_dict())
        self.prev_block_hash = self.bm.get_hash(my_genesis_block.to_dict())
        self.tp = TransactionPool()

        if core_node_host and core_node_port:
            self.plz_share_db()
        else:
            self.flag_stop_block_build = False

    def start_block_building(self):
        self.bb_timer = threading.Timer(CHECK_INTERVAL, self.__generate_block_with_tp)
        self.bb_timer.start()

    def stop_block_building(self):
        print('Thread for __generate_block_with_tp is stopped now')
        self.bb_timer.cancel()

    def start(self):
        self.server_state = STATE_STANDBY
        self.cm.start()
        self.start_block_building()

    def join_network(self):
        if self.core_node_host is not None:
            self.server_state = STATE_CONNECTED_TO_NETWORK  # 状態：親ノードへ接続中
            self.cm.join_network(self.core_node_host, self.core_node_port)
        else:
            print('This server is running as Genesis Core Node...')

    def shutdown(self):
        self.server_state = STATE_SHUTTING_DOWN  # 状態：切断中
        print('Shutdown server...')
        self.cm.connection_close()
        self.stop_block_building()

    def get_my_current_state(self):
        return self.server_state

    def plz_share_db(self):
        print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
        print("■■■■■■■■■■■■■■■■■■■■ plz_share_db ■■■■■■■■■■■■■■■■■■■■■■")
        print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
        new_message = self.cm.get_message_text(SHARE_DB3)
        self.cm.send_msg((self.core_node_host, self.core_node_port), new_message)
        print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")

    def get_all_chains_for_resolve_conflict(self):
        print('get_all_chains_for_resolve_conflict called')
        new_message = self.cm.get_message_text(MSG_REQUEST_FULL_CHAIN)
        self.cm.send_msg_to_all_peer(new_message)

    # def save_block_2_db(self):
    #     # if self.is_bb_running:
    #     #     self.flag_stop_block_build = True
    #     saved_bc = []
    #
    #     if len(self.bm.chain) >= SAVE_BORDER:
    #         saved_bc = self.bm.chain[:SAVE_BORDER_HALF]
    #         self.bm.chain = self.bm.chain[SAVE_BORDER_HALF:]
    #         main_level.add_db(ldb_p=LDB_P, param_p=PARAM_P, zip_p=ZIP_P, vals=saved_bc)
    #         print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
    #         print("保存しました")
    #         print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
    #
    #     # self.flag_stop_block_build = False

    def __generate_block_with_tp(self):
        if DEBUG:
            print('Thread for generate_block_with_tp started!')

        print("■■■■■■■■■■■■■■■■■■■ Current BC ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
        print(self.bm.chain)

        # self.save_block_2_db()
        saved_bcs = self.bm.save_block_2_db()

        print("txs_hash len:", self.tp.get_txs_hash_len())
        if saved_bcs:
            prev_ts = 0.0
            ts_list = []
            for saved_bc in saved_bcs:
                # genesis_blockはトランザクションがハッシュ値なのでloadsできない
                try:
                    self.tp.clear_my_hash_txs(json.loads(saved_bc["transactions"]))
                except json.decoder.JSONDecodeError:
                    pass

                if prev_ts == 0.0:
                    prev_ts = saved_bc["timestamp"]
                else:
                    ts_list.append(saved_bc["timestamp"] - prev_ts)
                    prev_ts = saved_bc["timestamp"]

            print("■■■■■■■■■■■■■■■■■■■")
            print("平均ブロック生成時間")
            print(sum(ts_list) / len(saved_bcs))
            print("■■■■■■■■■■■■■■■■■■■")

        print("txs_hash len:", self.tp.get_txs_hash_len())

        # while self.flag_stop_block_build is not True:
        if self.flag_stop_block_build is not True:
            # result = self.tp.get_stored_transactions()
            new_tp = self.tp.get_stored_transactions2()
            if DEBUG:
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                print("transactions", self.tp.get_stored_transactions())
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")

            # if not result:
            #     print('Transaction Pool is empty ...')
            #     new_block = self.bb.generate_new_block("", self.prev_block_hash)
            #     self.bm.set_new_block(new_block.to_dict())
            #     self.prev_block_hash = self.bm.get_hash(new_block.to_dict())
            #     # message_new_block = self.cm.get_message_text(MSG_NEW_BLOCK,
            #     #                                              json.dumps(new_block.to_dict(), sort_keys=True,
            #     #                                                         ensure_ascii=False))
            #     message_new_block = self.cm.get_message_text(MSG_NEW_BLOCK, json.dumps(new_block.to_dict()))
            #     self.cm.send_msg_to_all_peer(message_new_block)
            #     index = len(result)
            #     self.tp.clear_my_transactions(index)

            # TODO
            # new_tp = self.bm.remove_useless_transaction(result)
            # self.tp.renew_my_transactions(new_tp)

            # if len(new_tp) == 0:  # TODO TPが0のとき、終わるように。コメントアウトで切り替え
            #     break

            block_num = level_param.get_block_num(PARAM_P) + len(self.bm.chain)
            new_block = self.bb.generate_new_block(new_tp, self.prev_block_hash, str(block_num), ADDRESS, self)

            new_block_dic = new_block.to_dict()

            if not new_block_dic:
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■ 負け！w ■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                self.flag_stop_block_build = False
                self.is_bb_running = False
                self.bb_timer = threading.Timer(CHECK_INTERVAL, self.__generate_block_with_tp)
                self.bb_timer.start()
                return
            elif int(new_block_dic["block_number"]) <= int(self.bm.chain[-1]["block_number"]):
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■ YOU LOSE ■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                self.flag_stop_block_build = False
                self.is_bb_running = False
                self.bb_timer = threading.Timer(CHECK_INTERVAL, self.__generate_block_with_tp)
                self.bb_timer.start()
                return

            print("ブロック生成")
            print(new_block_dic)
            if len(self.bm.chain) >= 2:
                print("ブロック生成時間")
                print(self.__calculate_gene_time(self.bm.chain[-2], self.bm.chain[-1]))

            self.bm.set_new_block(new_block.to_dict())
            self.prev_block_hash = self.bm.get_hash(new_block.to_dict())

            # self.save_block_2_db()

            message_new_block = self.cm.get_message_text(MSG_NEW_BLOCK, json.dumps(new_block.to_dict()))

            self.cm.send_msg_to_all_peer(message_new_block)

            # index = len(result)
            # self.tp.clear_my_transactions(index)
            self.tp.clear_my_transactions2(new_tp)

            # break

        # print('Current prev_block_hash is ... ', self.prev_block_hash)
        self.flag_stop_block_build = False
        self.is_bb_running = False
        self.bb_timer = threading.Timer(CHECK_INTERVAL, self.__generate_block_with_tp)
        self.bb_timer.start()

    def __handle_message(self, msg, is_core, peer=None):

        if peer:
            if msg[2] == MSG_REQUEST_FULL_CHAIN:
                if DEBUG:
                    print('Send our latest blockchain for reply to : ', peer)
                mychain = self.bm.get_my_blockchain()
                if DEBUG:
                    print(mychain)
                chain_data = pickle.dumps(mychain, 0).decode()
                new_message = self.cm.get_message_text(RSP_FULL_CHAIN, chain_data)
                self.cm.send_msg(peer, new_message)
        else:
            if msg[2] == MSG_NEW_TRANSACTION:
                # 新規transactionを登録する処理を呼び出す
                new_transaction = json.loads(msg[4])
                if DEBUG:
                    print("received new_transaction", new_transaction)
                # current_transactions = self.tp.get_stored_transactions()

                # if DEBUG:
                #     print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                #     print("current_transactions:", current_transactions)
                #     print("current_transactions type:", type(current_transactions))
                #     if current_transactions:
                #         print("current_transactions [0]:", current_transactions[0])
                #         print("current_transactions [0] type:", type(current_transactions[0]))
                #     print("new_transaction:", new_transaction)
                #     print("new_transaction type:", type(new_transaction))
                #     if new_transaction:
                #         print("new_transaction [0]:", new_transaction[0])
                #         print("new_transaction [0]:", type(new_transaction[0]))
                #     print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

                # if new_transaction in current_transactions:
                #     if DEBUG:
                #         print("this is already pooled transaction:", new_transaction)
                #     return

                # only_new_tx = self.tp.check_duplicates(new_transaction)
                # if not only_new_tx:
                #     return

                if not self.tp.check_duplicates_and_set_tx(new_transaction):
                    return

                # self.tp.set_new_transaction(only_new_tx)

                if not is_core:
                    new_message = self.cm.get_message_text(MSG_NEW_TRANSACTION, json.dumps(new_transaction))
                    self.cm.send_msg_to_all_peer(new_message)

            elif msg[2] == MSG_NEW_BLOCK:

                if not is_core:
                    print('block received from unknown')
                    return

                # 新規ブロックを検証し、正当なものであればブロックチェーンに追加する

                new_block = json.loads(msg[4])
                if DEBUG:
                    print('new_block: ', new_block)

                if int(self.bm.chain[-1]["block_number"]) >= int(new_block["block_number"]):
                    return

                if self.bm.is_valid_block(self.prev_block_hash, new_block):
                    # ブロック生成が行われていたら一旦停止してあげる（threadingなのでキレイに止まらない場合あり）
                    if self.is_bb_running:
                        self.flag_stop_block_build = True

                    # self.prev_block_hash = self.bm.get_hash(new_block)
                    # self.bm.set_new_block(new_block)

                    if self.bm.set_new_block(new_block):
                        self.prev_block_hash = self.bm.get_hash(new_block)
                        self.tp.clear_my_transactions2(json.loads(new_block["transactions"]))
                        print("ブロック生成時間")
                        print(self.__calculate_gene_time(self.bm.chain[-2], self.bm.chain[-1]))

                    # self.bm.save_block_2_db()

                    self.flag_stop_block_build = False  # TODO 試しで追加

                else:
                    # ブロックとして不正ではないがcにコケる場合は自分がorphanブロックを生成している
                    # 可能性がある

                    self.get_all_chains_for_resolve_conflict()

            elif msg[2] == RSP_FULL_CHAIN:

                if not is_core:
                    if DEBUG:
                        print('blockchain received from unknown')
                    return
                # ブロックチェーン送信要求に応じて返却されたブロックチェーンを検証し、有効なものか検証した上で
                # 自分の持つチェインと比較し優位な方を今後のブロックチェーンとして有効化する
                new_block_chain = pickle.loads(msg[4].encode('utf8'))

                if (int(new_block_chain[-1]["block_number"]) > int(self.bm.chain[-1]["block_number"])) and \
                        ((int(new_block_chain[0]["block_number"]) == int(self.bm.chain[0]["block_number"])) or
                         (self.bm.chain[0]["block_number"] == "0")):
                    result, pool_4_orphan_blocks = self.bm.resolve_conflicts(new_block_chain)

                    if result and self.cm.sync_flag:
                        self.tp.justification_conflict(self.bm.chain[-6:])

                    if DEBUG:
                        print('blockchain received')
                    if result is not None:
                        self.prev_block_hash = result
                        # if len(pool_4_orphan_blocks) != 0:
                        #     # orphanブロック群の中にあった未処理扱いになるTransactionをTransactionPoolに戻す
                        #     new_transactions = self.bm.get_transactions_from_orphan_blocks(pool_4_orphan_blocks)
                        #     for t in new_transactions:
                        #         self.tp.set_new_transaction(t)
                    else:
                        if DEBUG:
                            print('Received blockchain is useless...')

                self.flag_stop_block_build = False  # TODO 試しで追加

            elif msg[2] == MSG_ENHANCED:
                # P2P Network を単なるトランスポートして使っているアプリケーションが独自拡張したメッセージはここで処理する。SimpleBitcoin としてはこの種別は使わない
                self.mpmh.handle_message(msg[4])

    def __get_myip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]

    def __calculate_gene_time(self, prev_block: dict, new_block: dict):
        prev_ts = prev_block["timestamp"]
        # prev_ts = 1587105439.753553
        new_ts = new_block["timestamp"]
        # new_ts = 1587105451.5021372
        gene_time = new_ts - prev_ts
        return gene_time
