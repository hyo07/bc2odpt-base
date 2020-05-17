# BC2ODPT
本コードは、[濵津 誠「ゼロから作る暗号通貨」 PEAKS](https://peaks.cc/books/cryptocurrency)にて公開されている[サンプルコード 03/04](https://github.com/peaks-cc/cryptocurrency-samplecode/tree/master/03/04)を元に新規実装、改良を行ったものです。  
  
BC2ODPTはブロックチェーン(BC)に公共交通オープンデータ(ODPT)のリアルタイムAPIから得られるデータを保存していくことで，その存在や遅延した事実を証明するアプリケーションとして作成をはじめました。  
  
現在は、ブロックチェーンを用いた研究を行うための、Bitcoinの一部機能を簡易的に模倣した、非常にベーシックな独自ブロックチェーンとして使っています。本システムの基幹部分は実装済みなため、基幹部分を本リポジトリに。研究・新規実装部分を[開発用リポジトリ](https://github.com/hyo07/bc2odpt-dev)に分けています（大学院講義での利用などの事情もあり）。

# 環境
- python: 3.7.3
- モジュール: requirements.txt 参照

# node
BC2ODPTには二種類のnodeがあります
# server_node
- PoWを行いブロックを生成、保存する役割を担います
- 指定の長さ以上のブロックはつながったブロックは/db/ldb/に保存されます
# client_node
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

## nodeB
- CONNECT_IP: 接続先IP
- CONNECT_PORT: 接続先port
  
その他はnodeAと同様

## clientA
- API_KEY: ODPTのAPIを用いる場合に仕様
- ADDRESS: トランザクションに含まれるアドレス名
  
その他AはnodeBと同様
