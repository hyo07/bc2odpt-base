import plyvel
import json
import binascii
import hashlib
from glob import glob


def get_last_block(s_num):
    p = "../db/{}/".format(str(s_num))
    db_list = list(glob(p + "block*.ldb"))
    last_file = sorted(db_list)[-1]
    re_s = []

    db = plyvel.DB(str(last_file), create_if_missing=False)
    for k, v in db:
        val = json.loads(v.decode())
        re_s.append(val)

    return re_s[-1]


def get_last_hash(s_num):
    last_block = get_last_block(s_num)
    return get_hash(last_block)


def _get_double_sha256(message):
    return hashlib.sha256(hashlib.sha256(message).digest()).digest()


def get_hash(block):
    block_string = json.dumps(block, sort_keys=True)
    return binascii.hexlify(_get_double_sha256(block_string.encode('utf-8'))).decode('ascii')


if __name__ == "__main__":
    S_NUM = 1
    print(get_last_hash(S_NUM))

    pass
