import plyvel
from glob import glob
import json
import binascii
import hashlib
import pprint


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

# 難易度調整版
def is_valid_block(prev_block_hash, block):
    # ブロック単体の正当性を検証する
    nonce = block['nonce']
    transactions = block['transactions']
    # addrs = block["addrs"]
    del block['nonce']
    del block['transactions']
    # del block['addrs']

    message = json.dumps(block, sort_keys=True)
    nonce = str(nonce)

    if block['previous_block'] != prev_block_hash:
        return False
    else:
        digest = binascii.hexlify(_get_double_sha256((message + nonce).encode('utf-8'))).decode('ascii')
        try:
            if int(digest, 16) <= int(block["target"], 16):
                block['nonce'] = nonce
                block['transactions'] = transactions
                # block["addrs"] = addrs
                return True
            else:
                return False
        except KeyError:
            if int(digest, 16) <= int(block["difficulty"], 16):
                block['nonce'] = nonce
                block['transactions'] = transactions
                # block["addrs"] = addrs
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
    return binascii.hexlify(_get_double_sha256(block_string.encode('utf-8'))).decode('ascii')


def comparison_ldbs(p1, p2, border=10):
    ldb1_list = sorted(list(glob(p1 + "block*.ldb")))
    ldb2_list = sorted(list(glob(p2 + "block*.ldb")))

    p1_name = p1.split("/")[-4]
    p2_name = p2.split("/")[-4]

    print(f"全ブロック長({p1_name[-1]}):", str(len(ldb1_list) * border))
    print(f"全ブロック長({p2_name[-1]}):", str(len(ldb2_list) * border))
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


# -----------------------------------------------------------------------------------------
def read_ones_db(p):
    db_list = list(glob(p + "block*.ldb"))
    total_tx = 0
    total_addr = 0
    clientA = 0
    clientB = 0
    clientC = 0
    clientD = 0
    clientE = 0
    clientF = 0
    clientG = 0
    clientH = 0
    clientI = 0
    clientJ = 0
    clientA2 = 0
    clientB2 = 0
    clientC2 = 0
    clientD2 = 0
    clientE2 = 0
    clientC3 = 0
    for db_name in sorted(db_list):
        db = plyvel.DB(str(db_name), create_if_missing=False)
        for k, v in db:
            # key = k.decode()
            val = json.loads(v.decode())
            total_tx += val.get("nTx", 0)
            total_addr += val.get("total_majority", 0)
            addr = val.get("addrs", None)
            if addr:
                addr_j = json.loads(addr)
                for in_addr in addr_j.values():
                    if "clientA" in in_addr["addrs"]:
                        clientA += 1
                    if "clientB" in in_addr["addrs"]:
                        clientB += 1
                    if "clientC" in in_addr["addrs"]:
                        clientC += 1
                    if "clientD" in in_addr["addrs"]:
                        clientD += 1
                    if "clientE" in in_addr["addrs"]:
                        clientE += 1
                    if "clientF" in in_addr["addrs"]:
                        clientF += 1
                    if "clientG" in in_addr["addrs"]:
                        clientG += 1
                    if "clientH" in in_addr["addrs"]:
                        clientH += 1
                    if "clientI" in in_addr["addrs"]:
                        clientI += 1
                    if "clientJ" in in_addr["addrs"]:
                        clientJ += 1
                    if "clientA2" in in_addr["addrs"]:
                        clientA2 += 1
                    if "clientB2" in in_addr["addrs"]:
                        clientB2 += 1
                    if "clientC2" in in_addr["addrs"]:
                        clientC2 += 1
                    if "clientD2" in in_addr["addrs"]:
                        clientD2 += 1
                    if "clientE2" in in_addr["addrs"]:
                        clientE2 += 1
                    if "clientC3" in in_addr["addrs"]:
                        clientC3 += 1
        db.close()
    # print(re_s)
    re_dic = {
        "total_tx": total_tx, "total_addr": total_addr,
        "clientA": clientA, "clientB": clientB, "clientC": clientC, "clientD": clientD, "clientE": clientE,
        "clientF": clientF, "clientG": clientG, "clientH": clientH, "clientI": clientI, "clientJ": clientJ,
        "clientA2": clientA2, "clientB2": clientB2, "clientC2": clientC2, "clientD2": clientD2, "clientE2": clientE2,
        "clientC3": clientC3,
    }
    return re_dic


def read_json_file(path="test.json"):
    with open(path, "r") as f:
        text = f.read()
        try:
            block_chain = json.loads(text)
        except:
            # re_hoge = text.replace("\'", "\"").replace("True", "true").replace("False", "false")
            # block_chain = json.loads(re_hoge)
            block_chain = eval(text)
    return block_chain


def read_logs(path, limit: int):
    import csv
    re_list = []
    log_pattern = ["*generate*", "*longest*", "*majority*"]
    for log_type in log_pattern:
        logs = glob(path + log_type)
        re_dic = {}
        for log in sorted(logs):
            file_name = log.split("/")[-1]
            with open(log, "r") as f:
                reader = csv.reader(f)
                count = 0
                for row in reader:
                    if int(row[1]) <= limit:
                        count += 1
                    else:
                        break
                re_dic[file_name] = count
        re_list.append(re_dic)
    return re_list


if __name__ == "__main__":
    pass

    import os

    root_P = os.path.dirname(os.path.abspath(__file__)) + "/.."
    P1 = root_P + "/nodeA/db/ldb/"
    P2 = root_P + "/nodeB/db/ldb/"
    P3 = root_P + "/nodeX_3/db/ldb/"
    P4 = root_P + "/nodeX_4/db/ldb/"
    P5 = root_P + "/nodeX_5/db/ldb/"

    read_bc = json_db(P1)
    # file読み
    # file_name = root_P + "/logs/20200929-1.json"
    # read_bc = read_json_file(file_name)

    # print(read_bc)
    print(len(read_bc))

    # with open(root_P + "/logs/20200924-2.json", "w") as f:
    #     f.write(json.dumps(read_bc))

    # print(len(read_bc))
    print(is_valid_chain(read_bc))
    # # print(valid_all(P1))
    #
    print("---------------------------------------------")
    #
    # diffチェック
    # print(comparison_ldbs(P1, P2, 20))
    # print(comparison_ldbs(P1, P3, 20))
    # print(comparison_ldbs(P1, P4, 20))
    # print(comparison_ldbs(P1, P5, 20))

    gene_time_list = []
    ts = 0
    for block in read_bc:
        if ts != 0:
            sa = block["timestamp"] - ts
            gene_time_list.append(sa)
        ts = block["timestamp"]
    print("平均:", sum(gene_time_list) / len(gene_time_list))

    # for block in read_bc:
    #     try:
    #         print(float(int(block["target"], 16)))
    #     except KeyError:
    #         print(float(int(block["difficulty"], 16)))

    pprint.pprint(read_logs(root_P + "/logs/", len(read_bc)))
