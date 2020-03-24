# kitenai

kintone上で管理している生徒が一定期間出席していないことを検知し、通知する。

## 説明

## 必須条件
- `Python 3.8.x` 以上 (`3.7.x` 以下では未検証。`2.x` 系では動作しない)
    - 利用モジュール
        - `requests`  
          以下でインストール  

            ```bash
            $ pip3 install requests
            ```
        - `slackclient`  
          以下でインストール  
          
            ```bash
            $ pip3 install slackclient
            ```
- [kintone](https://kintone.cybozu.co.jp/)（APIを利用するためにはスタンダード版の契約が必要）  

## 利用方法

### 1. kintone に「生徒マスタ」アプリと「出席管理」アプリを用意する
#### 「生徒マスタ」アプリ
- 必須フィールド  
  以下のフィールドは必須フィールドとして用意する  

    | フィールド名(任意) | フィールドタイプ | フィールドID | 説明 |
    |---|---|---|---|
    | 生徒番号 | RECORD_NUMBER | ID   | レコードナンバー(デフォルトで存在) |
    | 名前     | 文字列（1行）  | Name | 生徒名 |


#### 「出席管理」アプリ
- 必須フィールド  
  以下のフィールドは必須フィールドとして用意する  

    | フィールド名(任意) | フィールドタイプ | フィールドID | 説明 |
    |---|---|---|---|
    | レコード番号 | RECORD_NUMBER | ID         | レコードナンバー(デフォルトで存在) |
    | 生徒番号     | ルックアップ   | student_id | [生徒マスタ](#「生徒マスタ」アプリ) の「生徒番号」 |
    | 出席日時     | 日時          | attend_at  | 出席した日時 |

### 2. 設定ファイルの作成
[config.json.sample](config.json.sample) を `config.json` にリネームして利用する
- Slack で通知を受け取る場合の例  

    ```json
    {
        "kintone" : {
            "subdomain": "＜kintonenのサブドメイン（ドメインが hogefuga.cybozu.com なら「hogefuga」）＞",
            "student_app": "＜「生徒マスタ」アプリのID＞",
            "attend_app": "＜「出席管理」アプリのID＞",
            "student_token": "＜「生徒マスタ」アプリのアクセストークン＞",
            "attend_token": "＜「出席管理」アプリのアクセストークン＞"
        },
        "notify" : {
            "slack" : {
                "access_token": "＜利用ワークスペースのアプリのアクセストークン＞",
                "channel": "＜書き込むチャンネル（例：「#ramdom」）＞"
            }
        }
    }
    ```

### 3. 実行
```bash
$ python kitenai.py
```

## ユニットテスト

```shell
$ python -m unittest tests/test_kitenai.py
```
問題がなければ、以下のように表示される。
```
............
----------------------------------------------------------------------
Ran 12 tests in 0.001s

OK

```