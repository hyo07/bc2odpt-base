import signal
from time import sleep
import json
from random import randint

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

    transactions = []
    count = 1
    while True:
        value = randint(1, 100)
        # value = count
        transactions.append({
            'sender': 's{}'.format(str(count)),
            'recipient': 'r{}'.format(str(count)),
            'value': value,
            'client_address': ADDRESS,
        })
        if count % 10 == 0:
            my_p2p_client.send_message_to_my_core_node(MSG_NEW_TRANSACTION, json.dumps(transactions))
            transactions = []
            sleep(30)
            # count = 0
        else:
            sleep(1)
        count += 1

    # transactions = []
    # count = 1
    # while True:
    #     value = randint(1, 100)
    #     transactions.append({
    #         'sender': 's{}'.format(str(count)),
    #         'recipient': 'r{}'.format(str(count)),
    #         'value': value
    #     })
    #     if value < 34:
    #         my_p2p_client.send_message_to_my_core_node(MSG_NEW_TRANSACTION, json.dumps(transactions))
    #         transactions = []
    #         sleep(1)
    #     elif count % 10 == 0:
    #         my_p2p_client.send_message_to_my_core_node(MSG_NEW_TRANSACTION, json.dumps(transactions))
    #         transactions = []
    #         sleep(10)
    #     count += 1


if __name__ == '__main__':
    main()
