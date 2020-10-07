import plyvel
from glob import glob
import json
import binascii
import hashlib


# # ブロック番号とvalueを表示
# def print_db():
#     p = "../db/1/"
#     db_list = list(glob(p + "block*.ldb"))
#     s_l = []
#     for db_name in sorted(db_list):
#         db = plyvel.DB(str(db_name), create_if_missing=False)
#         for k, v in db:
#             key = k.decode()
#             val = v.decode()
#             mix = key + " => " + str(json.loads(val))
#             s_l.append(mix)
#
#     for s in sorted(s_l):
#         print(s)
#
#
# json形式で読み込み
def json_db(p):
    # p = "../db/2/ldb/"
    # p = "../db/1/ldb/"
    db_list = list(glob(p + "block*.ldb"))
    re_s = []
    for db_name in sorted(db_list):
        db = plyvel.DB(str(db_name), create_if_missing=False)
        for k, v in db:
            # key = k.decode()
            val = json.loads(v.decode())
            print(val)
            re_s.append(val)
        db.close()
    # print(re_s)
    return re_s


# １ファイルごとにJSON形式で読み込み。最後のブロックを保持しつつ次のファイル読んでいく
# かつ、整合性もチェックする
def valid_all(ldb_p):
    db_list = list(glob(ldb_p + "block*.ldb"))
    re_s = []
    for db_name in sorted(db_list):
        db = plyvel.DB(str(db_name), create_if_missing=False)
        for k, v in db:
            val = json.loads(v.decode())
            re_s.append(val)
        if not is_valid_chain(re_s):
            print("整合性が取れませんでした！！！！")
            return None
        re_s = re_s[-1:]
    if not re_s:
        print("ファイルが正常に読み込めませんでした")
        return None
    return re_s


# -------------------------------------------------------------------------------------------------------------------------

# 難易度調整版
def is_valid_block(prev_block_hash, block):
    # print("prev_block_hash:", prev_block_hash)
    # ブロック単体の正当性を検証する
    nonce = block['nonce']
    transactions = block['transactions']
    addrs = block["addrs"]
    del block['nonce']
    del block['transactions']
    del block['addrs']
    # print(block)

    message = json.dumps(block, sort_keys=True)
    # print("message", message)
    nonce = str(nonce)

    if block['previous_block'] != prev_block_hash:
        # print('Invalid block (bad previous_block)')
        # print(block['previous_block'])
        # print(prev_block_hash)
        return False
    else:
        digest = binascii.hexlify(_get_double_sha256((message + nonce).encode('utf-8'))).decode('ascii')
        if int(digest, 16) <= int(block["target"], 16):
            block['nonce'] = nonce
            block['transactions'] = transactions
            block["addrs"] = addrs
            return True
        else:
            return False


def is_valid_chain(chain):
    # ブロック全体の正当性を検証する
    last_block = chain[0]
    current_index = 1

    while current_index < len(chain):
        block = chain[current_index]
        if not is_valid_block(get_hash(last_block), block):
            return False

        last_block = chain[current_index]
        current_index += 1

    return True


def _get_double_sha256(message):
    return hashlib.sha256(hashlib.sha256(message).digest()).digest()


def get_hash(block):
    block_string = json.dumps(block, sort_keys=True)
    # print("BlockchainManager: block_string", block_string)
    return binascii.hexlify(_get_double_sha256((block_string).encode('utf-8'))).decode('ascii')


if __name__ == "__main__":
    pass
