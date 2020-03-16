import signal
from time import sleep
import json
from random import randint

from core.client_core import ClientCore
from p2p.message_manager import MSG_NEW_TRANSACTION

my_p2p_client = None


def signal_handler(signal, frame):
    shutdown_client()


def shutdown_client():
    global my_p2p_client
    my_p2p_client.shutdown()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    global my_p2p_client
    my_p2p_client = ClientCore(50095, '192.168.11.35', 50082)
    my_p2p_client.start()

    sleep(10)

    count = 1
    while True:
        transaction = {
            'sender': 's{}'.format(str(count)),
            'recipient': 'r{}'.format(str(count)),
            'value': randint(1, 100)
        }
        my_p2p_client.send_message_to_my_core_node(MSG_NEW_TRANSACTION, json.dumps(transaction))
        count += 1
        sleep(1)
        if count == 10:
            count = 0
            sleep(10)


if __name__ == '__main__':
    main()
