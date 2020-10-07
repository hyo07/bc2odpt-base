DEBUG = False  # True時、出力されるものが多くなる
TARGET = 5  # 初期targetの先頭に付く"0"の数
SAVE_BORDER = 40  # この値の大きさを超えたら半分セーブされる
SAVE_BORDER_HALF = 20  # SAVE_BORDERの1/2に設定する
THROUGH = 3  # 無視してかまわない
POW_TIME = 1  # ブロック生成の基準時間とする長さ[分]
TARGET_ADUJST = True  # 難易度調整のON・OFF
RAND_INTERVAL = False  # True時、INTERVALを毎回乱数にする
INTERVAL = 30  # ブロック生成後のクールダウン[s]
SKIP_INTERVAL = True  # True時、最初のDBへの保存までINTERVAL無視
ADDRESS = "nodeA"  # ブロックがどのnodeにて生成されたか判別するためのアドレス

HOST_PORT = 50082
