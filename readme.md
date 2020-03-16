# 環境
- python: 3.7.3
- モジュール: requirements.txt 参照

# 設定(setting.py)
## nodeA
- DEBUG: print表示の有無
- DIFFICULTY: マイニング難易度
- SAVE_BORDER: DBへ保存する際の閾値
- SAVE_BORDER_HALF: 実際に保存するライン
- HOST_PORT: 立ち上げport番号

## nodeB
- CONNECT_IP: 接続先IP
- CONNECT_PORT: 接続先port
  
その他はnodeAと同様

## clientA
API_KEY: ODPTのAPIを用いる場合に仕様
  
その他AはnodeBと同様
