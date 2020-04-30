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
            # print(val)
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
            print(re_s)
            print("整合性が取れませんでした！！！！")
            return None
        re_s = re_s[-1:]
    if not re_s:
        print("ファイルが正常に読み込めませんでした")
        return None
    return re_s


# -------------------------------------------------------------------------------------------------------------------------

def is_valid_block(prev_block_hash, block, difficulty=3):
    # print("prev_block_hash:", prev_block_hash)
    # ブロック単体の正当性を検証する
    suffix = '0' * difficulty
    nonce = block['nonce']
    transactions = block['transactions']
    del block['nonce']
    del block['transactions']
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
        if digest.endswith(suffix):
            # print('OK, this seems valid block')
            block['nonce'] = nonce
            block['transactions'] = transactions
            return True
        else:
            # print('Invalid block (bad nonce)')
            # print('nonce :', nonce)
            # print('digest :', digest)
            # print('suffix', suffix)
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
    return binascii.hexlify(_get_double_sha256(block_string.encode('utf-8'))).decode('ascii')


def comparison_ldbs(p1, p2, border=10):
    ldb1_list = sorted(list(glob(p1 + "block*.ldb")))
    ldb2_list = sorted(list(glob(p2 + "block*.ldb")))

    print("全ブロック長(nodeA):", str(len(ldb1_list) * border))
    print("全ブロック長(nodeB):", str(len(ldb2_list) * border))
    count = 0

    for (ldb1_db, ldb2_db) in zip(ldb1_list, ldb2_list):
        ldb1 = plyvel.DB(str(ldb1_db), create_if_missing=False)
        ldb2 = plyvel.DB(str(ldb2_db), create_if_missing=False)

        ldb1_list = []
        ldb2_list = []

        for k1, v1 in ldb1:
            ldb1_list.append(json.loads(v1.decode()))
        for k2, v2 in ldb2:
            ldb2_list.append(json.loads(v2.decode()))

        if ldb1_list != ldb2_list:
            print(ldb1_list)
            print(ldb2_list)
            print()
            count += 1

            # return False
    return count


if __name__ == "__main__":
    pass
    P1 = "/Users/yutaka/python/research/BC2ODPT/nodeA/db/ldb/"
    P2 = "/Users/yutaka/python/research/BC2ODPT/nodeB/db/ldb/"
    P3 = "/Users/yutaka/python/research/BC2ODPT/nodeX_3/db/ldb/"
    P4 = "/Users/yutaka/python/research/BC2ODPT/nodeX_4/db/ldb/"

    read_bc = json_db(P1)
    print(read_bc)
    # with open("/Users/yutaka/python/research/BC2ODPT/nodeA/4-show.json", "w") as f:
    #     f.write(str(read_bc))

    print(len(read_bc))
    print(is_valid_chain(read_bc))
    # print(valid_all(P1))

    # with open("test.txt", "w") as f:
    #     f.write(str(read_bc))

    # with open("memo.jslon", "w") as f:
    #     f.write(json.dumps(read_bc))

    print("---------------------------------------------")
    # J1 = json_db(P1)
    # J2 = json_db(P2)
    # print(J1 == J2)

    print(comparison_ldbs(P1, P2, 5))
    # print(comparison_ldbs(P1, P3, 5))
    # print(comparison_ldbs(P1, P4, 20))

    # a = []
    # for i in range(len(read_bc) - 1):
    #     try:
    #         tx = json.loads(read_bc[i]["transactions"])
    #         tx_count = len(tx)
    #     except json.decoder.JSONDecodeError:
    #         tx_count = 0
    #     ts = read_bc[i + 1]["timestamp"] - read_bc[i]["timestamp"]
    #     a.append(ts)
    #     print(ts)
    # print("平均:", sum(a)/len(a))
