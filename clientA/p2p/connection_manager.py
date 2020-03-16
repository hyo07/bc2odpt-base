import socket
import threading
import pickle
from concurrent.futures import ThreadPoolExecutor

import json
import binascii
import os

from .core_node_list import CoreNodeList
from .edge_node_list import EdgeNodeList
from .message_manager import (
    MessageManager,
    MSG_ADD,
    MSG_REMOVE,
    MSG_CORE_LIST,
    MSG_REQUEST_CORE_LIST,
    MSG_PING,
    MSG_ADD_AS_EDGE,
    MSG_REMOVE_EDGE,
    ERR_PROTOCOL_UNMATCH,
    ERR_VERSION_UNMATCH,
    OK_WITH_PAYLOAD,
    OK_WITHOUT_PAYLOAD,
    SHARE_DB3,
    SHARE_DB4,
    SHARE_DB5,
    SHARE_DB6,
    SHARE_DB7,
)

from libs import get_level_dir, level_param, check_level_all

# 動作確認用の値。本来は30分(1800)くらいがいいのでは
PING_INTERVAL = 10

dirname = os.path.dirname(__file__) + "/../db/"

LDB_P = dirname + "ldb/"
PARAM_P = dirname
ZIP_P = dirname + "zip/"

RE_LDB_P = dirname + "ldb/"
RE_PARAM_P = dirname
RE_ZIP_P = dirname + "zip/"


class ConnectionManager:

    def __init__(self, host, my_port, callback, sc_self=None):
        print('Initializing ConnectionManager...')
        self.host = host
        self.port = my_port
        self.my_c_host = None
        self.my_c_port = None
        self.core_node_set = CoreNodeList()
        self.edge_node_set = EdgeNodeList()
        self.__add_peer((host, my_port))
        self.mm = MessageManager()
        self.callback = callback
        self.sc_self = sc_self
        self.flag = 0

    # 待受を開始する際に呼び出される（ServerCore向け
    def start(self):
        t = threading.Thread(target=self.__wait_for_access)
        t.start()

        self.ping_timer_p = threading.Timer(PING_INTERVAL, self.__check_peers_connection)
        self.ping_timer_p.start()

        self.ping_timer_e = threading.Timer(PING_INTERVAL, self.__check_edges_connection)
        self.ping_timer_e.start()

    # ユーザが指定した既知のCoreノードへの接続（ServerCore向け
    def join_network(self, host, port):
        self.my_c_host = host
        self.my_c_port = port
        self.__connect_to_P2PNW(host, port)

    def get_message_text(self, msg_type, payload=None):
        """
        指定したメッセージ種別のプロトコルメッセージを作成して返却する
        
        params:
            msg_type : 作成したいメッセージの種別をMessageManagerの規定に従い指定
            payload : メッセージにデータを格納したい場合に指定する
        
        return:
            msgtxt : MessageManagerのbuild_messageによって生成されたJSON形式のメッセージ
        """
        msgtxt = self.mm.build(msg_type, self.port, payload)
        print('generated_msg:', msgtxt)
        return msgtxt

    # 指定されたノードに対してメッセージを送信する
    def send_msg(self, peer, msg):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(peer)
            print(peer)
            s.sendall(msg.encode('utf-8'))
            s.close()
        except OSError:
            print('Connection failed for peer : ', peer)
            self.__remove_peer(peer)

    # Coreノードリストに登録されている全てのノードに対して同じメッセージをブロードキャストする
    def send_msg_to_all_peer(self, msg):
        print('send_msg_to_all_peer was called!')
        current_list = self.core_node_set.get_list()
        for peer in current_list:
            if peer != (self.host, self.port):
                print("message will be sent to ... ", peer)
                self.send_msg(peer, msg)

    # Edgeノードリストに登録されている全てのノードに対して同じメッセージをブロードキャストする
    def send_msg_to_all_edge(self, msg):
        print('send_msg_to_all_edge was called! ')
        current_list = self.edge_node_set.get_list()
        for edge in current_list:
            print("message will be sent to ... ", edge)
            self.send_msg(edge, msg)

    # 終了前の処理としてソケットを閉じる
    def connection_close(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        self.socket.close()
        s.close()
        self.ping_timer_p.cancel()
        self.ping_timer_e.cancel()
        # 離脱要求の送信
        if self.my_c_host is not None:
            msg = self.mm.build(MSG_REMOVE, self.port)
            self.send_msg((self.my_c_host, self.my_c_port), msg)

    def __connect_to_P2PNW(self, host, port):
        msg = self.mm.build(MSG_ADD, self.port)
        self.send_msg((host, port), msg)

    def __wait_for_access(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(0)

        executor = ThreadPoolExecutor(max_workers=10)

        while True:
            print('Waiting for the connection ...')
            soc, addr = self.socket.accept()
            print('Connected by .. ', addr)
            data_sum = ''

            params = (soc, addr, data_sum)
            executor.submit(self.__handle_message, params)

    def __is_in_core_set(self, peer):
        """
        与えられたnodeがCoreノードのリストに含まれているか？をチェックする

            param:
                peer : IPアドレスとポート番号のタプル
            return:
                True or False
        """
        return self.core_node_set.has_this_peer(peer)

    # 受信したメッセージを確認して、内容に応じた処理を行う。クラスの外からは利用しない想定
    def __handle_message(self, params):

        soc, addr, data_sum = params

        while True:
            data = soc.recv(1024)
            data_sum = data_sum + data.decode('utf-8')

            if not data:
                break

        if not data_sum:
            return

        result, reason, cmd, peer_port, payload = self.mm.parse(data_sum)
        print(result, reason, cmd, peer_port, payload)
        status = (result, reason)

        if status == ('error', ERR_PROTOCOL_UNMATCH):
            print('Error: Protocol name is not matched')
            return
        elif status == ('error', ERR_VERSION_UNMATCH):
            print('Error: Protocol version is not matched')
            return
        elif status == ('ok', OK_WITHOUT_PAYLOAD):
            if cmd == MSG_ADD:
                print('ADD node request was received!!')
                self.__add_peer((addr[0], peer_port))
                if (addr[0], peer_port) == (self.host, self.port):
                    return
                else:
                    cl = pickle.dumps(self.core_node_set.get_list(), 0).decode()
                    msg = self.mm.build(MSG_CORE_LIST, self.port, cl)
                    self.send_msg_to_all_peer(msg)
                    self.send_msg_to_all_edge(msg)
            elif cmd == MSG_REMOVE:
                print('REMOVE request was received!! from', addr[0], peer_port)
                self.__remove_peer((addr[0], peer_port))
                cl = pickle.dumps(self.core_node_set.get_list(), 0).decode()
                msg = self.mm.build(MSG_CORE_LIST, self.port, cl)
                self.send_msg_to_all_peer(msg)
                self.send_msg_to_all_edge(msg)
            elif cmd == MSG_PING:
                # 特にやること思いつかない
                return
            elif cmd == MSG_REQUEST_CORE_LIST:
                print('List for Core nodes was requested!!')
                cl = pickle.dumps(self.core_node_set.get_list(), 0).decode()
                msg = self.mm.build(MSG_CORE_LIST, self.port, cl)
                self.send_msg((addr[0], peer_port), msg)
            elif cmd == MSG_ADD_AS_EDGE:
                self.__add_edge_node((addr[0], peer_port))
                cl = pickle.dumps(self.core_node_set.get_list(), 0).decode()
                msg = self.mm.build(MSG_CORE_LIST, self.port, cl)
                self.send_msg((addr[0], peer_port), msg)
            elif cmd == MSG_REMOVE_EDGE:
                print('REMOVE_EDGE request was received!! from', addr[0], peer_port)
                self.__remove_edge_node((addr[0], peer_port))

            elif cmd == SHARE_DB3:
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■ SHARE_DB3 handle ■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                cl = str(get_level_dir.get_late_dir_num(zip_p=ZIP_P))
                msg = self.mm.build(SHARE_DB4, self.port, cl)
                self.send_msg((addr[0], peer_port), msg)
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")

            elif cmd == SHARE_DB4:
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■ SHARE_DB4 handle ■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                new_node_dir = int(get_level_dir.get_late_dir_num(zip_p=RE_ZIP_P))
                latest_dir = int(json.loads(data_sum)["payload"])
                if new_node_dir < latest_dir:
                    cl = new_node_dir + 1
                    self.flag = 0
                    msg = self.mm.build(SHARE_DB5, self.port, cl)
                    self.send_msg((addr[0], peer_port), msg)
                else:
                    if self.flag == 0:
                        get_level_dir.unfold_zip_dir(ldb_p=RE_LDB_P, zip_p=RE_ZIP_P)
                        level_param.update_key(RE_PARAM_P, level_param.latest_block_num(RE_LDB_P))
                        latest_db_bc = check_level_all.valid_all(RE_LDB_P)
                    else:
                        latest_db_bc = check_level_all.valid_all(RE_LDB_P)
                    if latest_db_bc:
                        print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                        print("DB Valid Check OK !!!!")
                        print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                        if self.flag == 0:
                            print("■■■■■■■■ Start Share  ■■■■■■■■■")
                            self.sc_self.get_all_chains_for_resolve_conflict()
                            self.flag = 1

                        if "genesis_block" in self.sc_self.bm.chain[0]:
                            msg = self.mm.build(SHARE_DB5, self.port, str(latest_dir))
                            self.send_msg((addr[0], peer_port), msg)
                        elif not check_level_all.is_valid_chain([latest_db_bc[0], self.sc_self.bm.chain[0]]):
                            msg = self.mm.build(SHARE_DB5, self.port, str(latest_dir))
                            self.send_msg((addr[0], peer_port), msg)
                        else:
                            if check_level_all.is_valid_chain([latest_db_bc[0], self.sc_self.bm.chain[0]]):
                                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                                print("DB2Memory Valid Check OK !!!!")
                                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                                msg = self.mm.build(SHARE_DB7, self.port)
                                self.send_msg((addr[0], peer_port), msg)

                    else:
                        print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                        print("■■■■■■■■ WARNING ■■■■■■■■■ WARNING ■■■■■■■■ WARNING ■■■■■■■■■")
                        print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")

                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")

            elif cmd == SHARE_DB5:
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■ SHARE_DB5 handle ■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                receive_dir_num = str(json.loads(data_sum)["payload"])
                re_dir = receive_dir_num.zfill(6)
                p = ZIP_P + "block{}.zip".format(re_dir)
                with open(p, mode="rb") as z:
                    z_file = z.read()
                cl = z_file.hex()
                msg = self.mm.build(SHARE_DB6, self.port, cl)
                self.send_msg((addr[0], peer_port), msg)
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")

            elif cmd == SHARE_DB6:
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■ SHARE_DB6 handle ■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                payload = json.loads(data_sum)["payload"]
                latest_dir = int(get_level_dir.get_late_dir_num(zip_p=RE_ZIP_P)) + 1
                p = RE_ZIP_P + "block{}.zip".format(str(latest_dir).zfill(6))
                with open(p, mode="wb") as rz:
                    rz.write(binascii.unhexlify(payload))
                msg = self.mm.build(SHARE_DB3, self.port)
                self.send_msg((addr[0], peer_port), msg)
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")

            elif cmd == SHARE_DB7:
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■ SHARE_D7B7 handle ■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
                print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")


            else:
                is_core = self.__is_in_core_set((addr[0], peer_port))
                self.callback((result, reason, cmd, peer_port, payload), is_core, (addr[0], peer_port))
                return
        elif status == ('ok', OK_WITH_PAYLOAD):
            if cmd == MSG_CORE_LIST:
                # TODO: 受信したリストをただ上書きしてしまうのは本来セキュリティ的には宜しくない。
                # 信頼できるノードの鍵とかをセットしとく必要があるかも
                # このあたりの議論については６章にて補足予定
                print('Refresh the core node list...')
                new_core_set = pickle.loads(payload.encode('utf8'))
                print('latest core node list: ', new_core_set)
                self.core_node_set.overwrite(new_core_set)
            else:
                is_core = self.__is_in_core_set((addr[0], peer_port))
                self.callback((result, reason, cmd, peer_port, payload), is_core, None)
                return
        else:
            print('Unexpected status', status)

    def __add_peer(self, peer):
        """
        Coreノードをリストに追加する。クラスの外からは利用しない想定

        param:
            peer : Coreノードとして格納されるノードの接続情報（IPアドレスとポート番号）
        """
        self.core_node_set.add((peer))

    def __add_edge_node(self, edge):
        """
        Edgeノードをリストに追加する。クラスの外からは利用しない想定

        param:
            edge : Edgeノードとして格納されるノードの接続情報（IPアドレスとポート番号）
        """
        self.edge_node_set.add((edge))

    def __remove_peer(self, peer):
        """
        離脱したと判断されるCoreノードをリストから削除する。クラスの外からは利用しない想定

        param:
            peer : 削除するノードの接続先情報（IPアドレスとポート番号）
        """
        self.core_node_set.remove(peer)

    def __remove_edge_node(self, edge):
        """
        離脱したと判断されるEdgeノードをリストから削除する。クラスの外からは利用しない想定

        param:
            edge : 削除するノードの接続先情報（IPアドレスとポート番号）
        """
        self.edge_node_set.remove(edge)

    def __check_peers_connection(self):
        """
        接続されているCoreノード全ての生存確認を行う。クラスの外からは利用しない想定
        この確認処理は定期的に実行される
        """
        print('check_peers_connection was called')
        current_core_list = self.core_node_set.get_list()
        changed = False
        dead_c_node_set = list(filter(lambda p: not self.__is_alive(p), current_core_list))
        if dead_c_node_set:
            changed = True
            print('Removing peer', dead_c_node_set)
            current_core_list = current_core_list - set(dead_c_node_set)
            self.core_node_set.overwrite(current_core_list)

        current_core_list = self.core_node_set.get_list()
        print('current core node list:', current_core_list)
        # 変更があった時だけブロードキャストで通知する
        if changed:
            cl = pickle.dumps(current_core_list, 0).decode()
            msg = self.mm.build(MSG_CORE_LIST, self.port, cl)
            self.send_msg_to_all_peer(msg)
            self.send_msg_to_all_edge(msg)
        self.ping_timer_p = threading.Timer(PING_INTERVAL, self.__check_peers_connection)
        self.ping_timer_p.start()

    def __check_edges_connection(self):
        """
        接続されているEdgeノード全ての生存確認を行う。クラスの外からは利用しない想定
        この確認処理は定期的に実行される
        """
        print('check_edges_connection was called')
        current_edge_list = self.edge_node_set.get_list()
        dead_e_node_set = list(filter(lambda p: not self.__is_alive(p), current_edge_list))
        if dead_e_node_set:
            print('Removing Edges', dead_e_node_set)
            current_edge_list = current_edge_list - set(dead_e_node_set)
            self.edge_node_set.overwrite(current_edge_list)

        current_edge_list = self.edge_node_set.get_list()
        print('current edge node list:', current_edge_list)
        self.ping_timer_e = threading.Timer(PING_INTERVAL, self.__check_edges_connection)
        self.ping_timer_e.start()

    def __is_alive(self, target):
        """
        有効ノード確認メッセージの送信

        param:
            target : 有効ノード確認メッセージの送り先となるノードの接続情報（IPアドレスとポート番号）
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target))
            msg_type = MSG_PING
            msg = self.mm.build(msg_type)
            s.sendall(msg.encode('utf-8'))
            s.close()
            return True
        except OSError:
            return False
