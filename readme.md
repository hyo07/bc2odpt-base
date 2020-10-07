# BC2ODPT
本コードは、[濵津 誠「ゼロから作る暗号通貨」 PEAKS](https://peaks.cc/books/cryptocurrency)にて公開されている[サンプルコード 03/04](https://github.com/peaks-cc/cryptocurrency-samplecode/tree/master/03/04)を元に新規実装、改良を行ったものです。  
  
BC2ODPTはブロックチェーン(BC)に公共交通オープンデータ(ODPT)のリアルタイムAPIから得られるデータを保存していくことで，その存在や遅延した事実を証明するアプリケーションとして作成をはじめました。  
  
現在は、ブロックチェーンを用いた研究を行うための、Bitcoinの一部機能を簡易的に模倣した、非常にベーシックな独自ブロックチェーンとして使っています。本システムの基幹部分は実装済みなため、基幹部分を本リポジトリに。研究・新規実装部分を[開発用リポジトリ](https://github.com/hyo07/bc2odpt-dev)に分けています（大学院講義での利用などの事情もあり）。

# 環境
- python: 3.7.3
- モジュール: requirements.txt 参照

# node
BC2ODPTには二種類のnodeがあります
## server_node
- PoWを行いブロックを生成、保存する役割を担います
- 指定の長さ以上のブロックはつながったブロックは/db/ldb/に保存されます
## client_node
- server_nodeにトランザクションを送信する役割を担います

# 設定(setting.py)
各node/setting.pyにてパラメータや接続設定などを行います。
## nodeA
- DEBUG: print表示の有無
- DIFFICULTY: マイニング難易度
- SAVE_BORDER: DBへ保存する際の閾値
- SAVE_BORDER_HALF: 実際に保存するライン
- HOST_PORT: 立ち上げport番号
- ADDRESS: ブロックに含まれるアドレス名
- THROUGH: bc2odpt-devで使用。こちらでは無効化されているので意味はない
- POW_TIME: 難易度の自動調整をするとき、基準としてブロック生成のされる目安とする時間（分）
- TARGET_ADUJST: 難易度自動調整のON・OFF
- RAND_INTERVAL: INTERVALの値を乱数にする（node間にてブロック生成時間をばらけさせたい場合に使用）
- INTERVAL: インターバルとしてブロック生成後に何もせず待機する時間（秒）
- SKIP_INTERVAL: 最初のDBへのブロック保存までインターバルを0秒にする（nodeAのみ）

## nodeB
- CONNECT_IP: 接続先IP
- CONNECT_PORT: 接続先port
  
その他はnodeAと同様

## clientA
- API_KEY: ODPTのAPIを用いる場合に仕様
- ADDRESS: トランザクションに含まれるアドレス名
  
その他AはnodeBと同様

# その他ディレクトリ
## logs
ログが出力されます。  
一部処理無内でのerrorログ、およびブロック生成・ブロックチェーン上書き発生時にログが発生します。
- `node*_error_*.log`: エラーログ
- `*_generate_block.csv`: ブロックが生成されたというログ（`server_core.py` 284行目参照）
- `*_most_longest.csv`: 自身の持つものより長いブロックチェーンに上書きされたというログ（`server_core.py` 392行目参照）


# 実行手順
## 事前準備
各種`setting.py`にてパラーメータ・IP・portなどを正しく設定する必要あり。

## 最初のnode
一番最初のnodeとして、`nodeA/server1.py` を実行する。  
そうすると、PoWを始めブロックを生成し続ける。  
`setting.py` にて設定した`SAVE_BORDER` のブロック長を超えるとセーブされる。ここで最初のDBへの保存がされて以降、他のnodeが参加できる（正格にはそれ以前から参加可能だが、DBの共有がこちらのがわかりやすい）。

## 新規接続node
新規接続nodeとして、`nodeB/server2.py`を実行する。  
nodeB以外にも、nodeBを複製して新規接続nodeとして増やすことは可能。その際も`server2.py`を実行する。  
  
新規接続の際、ブロック同期の前にその新規node内だけでのgenesisブロックを生成し、それから同期が開始します（本当はこの工程を省きたいですが放置になっています）。  
同期開始後、`DB Valid Memory` という出力がされたらDB・メモリ両方のブロックの同期が完了です。  

## クライアントnode
`clientA/client_per_10.py`などを実行。  
各種clientのプログラムは実験用に複数のtxを送信しているが、ただtxの中身が違うだけで送信方法は全て同じ。

# 送信するトランザクションの設定方法
トランザクションの送信自体は`clientA/client_*.py`にて行われている。  
これらのプログラムには以下の処理がされており、  
```my_p2p_client.send_message_to_my_core_node(MSG_NEW_TRANSACTION, json.dumps(transaction))```  
この`transaction`が、実際に送信されるオブジェクトとなる。  
  
形式としてははJSON形式となっており、この形式であればどのような内容でも送信が可能（なはず）。