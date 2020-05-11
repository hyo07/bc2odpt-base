import plyvel
from pathlib import Path
import json
from libs import level_param
import shutil
from glob import glob


def add_db(ldb_p, param_p, zip_p, vals: list):
    p = Path(ldb_p)

    db_list = list(p.glob("block*.ldb"))
    file_count = len(db_list)
    file_num = str(file_count + 1).zfill(6)
    make_ldb_path = ldb_p + "block{}.ldb".format(str(file_num))

    for val in vals:
        lated_bl_num = level_param.get_block_num(param_p=param_p)
        level_param.update_key(param_p=param_p, block_num=lated_bl_num + 1)

        str_val = json.dumps(val)

        db = plyvel.DB(make_ldb_path, create_if_missing=True)
        db.put(str(lated_bl_num + 1).zfill(6).encode(), str_val.encode())
        db.close()

    shutil.make_archive(zip_p + "block{}".format(str(file_num)), "zip", root_dir=make_ldb_path)


def get_genesis(p):
    db_list = sorted(list(glob(p + "block*.ldb")))
    if not db_list:
        return False
    oldest_dbd = db_list[0]
    db = plyvel.DB(str(oldest_dbd), create_if_missing=False)
    gene = None
    for k, v in db:
        gene = json.loads(v.decode())
        break
    db.close()
    if gene["genesis_block"] is True:
        return True
    else:
        return False


def get_latest_block(p):
    db_list = sorted(list(glob(p + "block*.ldb")))
    latest_dbd = db_list[-1]
    db = plyvel.DB(str(latest_dbd), create_if_missing=False)
    val = None
    for k, v in db:
        val = json.loads(v.decode())
    db.close()
    return val


if __name__ == "__main__":
    pass

    get_genesis("a")
