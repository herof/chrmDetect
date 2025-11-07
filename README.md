# Chime Detector with SwitchBot Integration

音を検知してSwitchBotデバイスを自動制御するプログラムです。

## 機能

- マイクから音を検知
- 特定の周波数帯域（800-2000Hz）の音を感知
- 音を検知したらSwitchBot APIを呼び出してデバイスを制御

## セットアップ

### 1. 必要なパッケージのインストール

```bash
pip install sounddevice numpy requests
```

### 2. SwitchBot APIトークンの取得

1. SwitchBotアプリを開く
2. プロフィール > 設定 に移動
3. 「アプリバージョン」を10回タップ
4. 「開発者向けオプション」が表示される
5. 「トークンを取得」をタップしてトークンをコピー

### 3. デバイスIDの取得

以下のコマンドでデバイス一覧を取得:

```bash
curl -X 'GET' 'https://api.switch-bot.com/v1.0/devices' \
  -H 'accept: application/json' \
  -H 'Authorization: YOUR_TOKEN'
```

レスポンスの`body.deviceList`から制御したいデバイスの`deviceId`をコピーしてください。

### 4. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成:

```bash
cp .env.example .env
```

`.env`ファイルを編集して、トークンとデバイスIDを設定:

```
SWITCHBOT_TOKEN=your_actual_token
SWITCHBOT_DEVICE_ID=your_actual_device_id
```

環境変数を読み込んで実行:

```bash
export $(cat .env | xargs) && python main.py
```

## 使い方

プログラムを実行すると、マイクからの音を監視し始めます:

```bash
python main.py
```

音を検知すると:
1. "🔔 音を感知しました！！" と表示
2. SwitchBot APIを呼び出してデバイスをONにする
3. 3秒間のクールダウン期間（連続検知を防ぐ）

## カスタマイズ

### 検知パラメータの調整

`main.py`の以下の定数を変更できます:

- `DB_THRESH`: 音量の閾値（デフォルト: -25dB）
- `BAND`: 検知する周波数帯域（デフォルト: 800-2000Hz）
- `cool_down`: クールダウン時間（デフォルト: 3秒）

### SwitchBotコマンドの変更

`on_chime_detected()`関数内のコマンドを変更できます:

```python
# ONにする
call_switchbot_api(SWITCHBOT_DEVICE_ID, "turnOn")

# OFFにする
call_switchbot_api(SWITCHBOT_DEVICE_ID, "turnOff")

# ボタンを押す（Bot デバイスの場合）
call_switchbot_api(SWITCHBOT_DEVICE_ID, "press")
```

## 対応デバイス

- Bot（スイッチボット）
- Plug（プラグ）
- Plug Mini
- その他のSwitchBot物理デバイス

詳細は[SwitchBot API v1.0ドキュメント](https://github.com/OpenWonderLabs/SwitchBotAPI/blob/main/README-v1.0.md)を参照してください。

## トラブルシューティング

### マイクが見つからない

`sd.default.device`の設定を確認してください。利用可能なデバイスを確認:

```python
import sounddevice as sd
print(sd.query_devices())
```

### API呼び出しが失敗する

- トークンが正しいか確認
- デバイスIDが正しいか確認
- デバイスがオンラインか確認
- ネットワーク接続を確認

## 参考資料

- [SwitchBot API v1.0](https://github.com/OpenWonderLabs/SwitchBotAPI/blob/main/README-v1.0.md)
- [OpenAPIを用いてSwitchbot Hubのデータを取得する](https://qiita.com/ndil_hottay/items/90cfad509474e7e75e72)
