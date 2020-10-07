import json
import signal
from datetime import datetime
from time import sleep

from core.client_core import ClientCore
from p2p.message_manager import MSG_NEW_TRANSACTION
from setting import *

my_p2p_client = None


def signal_handler(signal, frame):
    shutdown_client()


def shutdown_client():
    global my_p2p_client
    my_p2p_client.shutdown()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    global my_p2p_client
    my_p2p_client = ClientCore(HOST_PORT, CONNECT_IP, CONNECT_PORT)
    my_p2p_client.start()

    sleep(10)

    while True:
        count = 0
        txs = []
        while True:
            dt = datetime.now()
            str_dt = dt.strftime("%Y-%m-%d %H:%M:%S")[:-1]
            transaction = {
                'datetime': str_dt + "0",
                'client_address': ADDRESS,
                "attack": False
            }
            txs.append(transaction)
            sleep(10)
            count += 1

            if count >= 10:
                my_p2p_client.send_message_to_my_core_node(MSG_NEW_TRANSACTION, json.dumps(txs))
                count = 0
                txs = []


if __name__ == '__main__':
    main()
