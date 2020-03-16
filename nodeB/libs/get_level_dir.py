from glob import glob
import zipfile


# 最新のディレクトリ番号を見る
def get_late_dir_num(zip_p):
    db_list = sorted(list(glob(zip_p + "block*.zip")))
    if not db_list:
        return 0

    latest_dir = db_list[-1].split("/")[-1]
    return int(latest_dir[5:-4])


# zipディレクトリを全て展開する
def unfold_zip_dir(ldb_p, zip_p):
    db_list = sorted(list(glob(zip_p + "block*.zip")))

    for zip_dir in db_list:
        dir_name = zip_dir[-10:-4] + ".ldb"
        with zipfile.ZipFile(zip_dir, "r") as zf:
            # zf.extractall("../db/{}/ldb/block{}".format(str(s_num), dir_name))
            zf.extractall("{}block{}".format(ldb_p, dir_name))


if __name__ == "__main__":
    pass

    print(get_late_dir_num("../db/1/zip/"))
