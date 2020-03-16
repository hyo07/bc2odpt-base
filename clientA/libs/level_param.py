import plyvel
from glob import glob


def update_key(param_p, block_num):
    db = plyvel.DB(param_p + "param.ldb", create_if_missing=True)
    db.put("block_num".encode(), str(block_num).zfill(6).encode())
    db.close()


def get_block_num(param_p):
    try:
        db = plyvel.DB(param_p + "param.ldb", create_if_missing=True)
    except plyvel._plyvel.Error:
        return 0

    block_num = db.get("block_num".encode())
    db.close()
    if block_num:
        block_num = block_num.decode()
        return int(block_num.lstrip("0"))
    else:
        return 0


def latest_block_num(ldb_p):
    db_list = sorted(list(glob(ldb_p + "block*.ldb")))
    if not db_list:
        return "000000"
    db = plyvel.DB(db_list[-1], create_if_missing=True)
    block_num = "0"
    for k, v in db:
        if block_num < k.decode():
            block_num = k.decode()
    return block_num


if __name__ == "__main__":
    pass

    # db = plyvel.DB("../db/1/param", create_if_missing=False)
    # for k, v in db:
    #     print(k.decode())
    #     print(v.decode())

    print(latest_block_num("../db/2/ldb/"))
