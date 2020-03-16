import plyvel
from pathlib import Path
import json
from libs import level_param
import shutil


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


if __name__ == "__main__":
    pass
    j = [
        {
            'transactions': 'AD9B477B42B22CDF18B1335603D07378ACE83561D8398FBFC8DE94196C65D806',
            'genesis_block': True,
            'nonce': '718'
        },
        {
            'timestamp': 1571809685.3452349,
            'transactions': [],
            'previous_block': '69b9921b393eb65ecd6d55398b901e6cc810c8a9b052591bcf920058d03fa162',
            'nonce': '2033'
        },
        {
            'timestamp': 1571809695.3835788,
            'transactions': [
                '{"sender": "s1", "recipient": "r1", "value": 99}',
                '{"sender": "s2", "recipient": "r2", "value": 39}',
                '{"sender": "s3", "recipient": "r3", "value": 31}'
            ],
            'previous_block': '6295dc03eee9ce4f908432ae519ce3256151696644593ca46d4dc2f85048f82d',
            'nonce': '1016'
        },
        {
            'timestamp': 1571809705.416286,
            'transactions': [
                '{"sender": "s4", "recipient": "r4", "value": 87}',
                '{"sender": "s5", "recipient": "r5", "value": 27}'
            ],
            'previous_block': '86baae6137c699304af6dea0d6eaf628fe68bcbc88d2ea7ca26bf8205e60db82',
            'nonce': '1280'
        },
        {
            'timestamp': 1571809715.450429,
            'transactions': [
                '{"sender": "s6", "recipient": "r6", "value": 10}',
                '{"sender": "s7", "recipient": "r7", "value": 2}',
                '{"sender": "s8", "recipient": "r8", "value": 45}'
            ],
            'previous_block': '37e7d97261dcda86cf38fb8a2d1cc431092a5b78c9e4b6f6883f44989895b48a',
            'nonce': '5889'
        },
        {
            'timestamp': 1571809725.494622,
            'transactions': [
                '{"sender": "s9", "recipient": "r9", "value": 98}',
                '{"sender": "s10", "recipient": "r10", "value": 25}'
            ],
            'previous_block': '5354905527270a35b332b73854a074f46ed2fce77565785c8a35626599171b32',
            'nonce': '4662'
        },
        {
            'timestamp': 1571809735.526561,
            'transactions': [
                '{"sender": "s11", "recipient": "r11", "value": 93}',
                '{"sender": "s12", "recipient": "r12", "value": 47}',
                '{"sender": "s13", "recipient": "r13", "value": 78}'
            ],
            'previous_block': 'b2cc09742350fa4c626ab9b1fb147f0e9bf89ac94466c8d7dbfab13195dd5f2c',
            'nonce': '2206'
        },
        {
            'timestamp': 1571809745.5499609,
            'transactions': [
                '{"sender": "s14", "recipient": "r14", "value": 9}',
                '{"sender": "s15", "recipient": "r15", "value": 21}'
            ],
            'previous_block': '3132f90ee5f363d1bee5edad1f7d3a63f9aabcd103de4a5b7f31fbc41bbbd77c',
            'nonce': '6282'
        },
        {
            'timestamp': 1571809755.588211,
            'transactions': [
                '{"sender": "s16", "recipient": "r16", "value": 59}',
                '{"sender": "s17", "recipient": "r17", "value": 47}',
                '{"sender": "s18", "recipient": "r18", "value": 47}'
            ],
            'previous_block': '0b1c106c8c14f0f188cef15058d6e158c38fea8fca94907017c2d5494213c4c2',
            'nonce': '1521'
        },
        {
            'timestamp': 1571809765.6007712,
            'transactions': [
                '{"sender": "s19", "recipient": "r19", "value": 74}',
                '{"sender": "s20", "recipient": "r20", "value": 39}'
            ],
            'previous_block': '67ad8cbc9b32c3c3921b3aa75e3a8c9b4741dcaa6a865ff5a1da477c63861faf',
            'nonce': '397'
        }
    ]
