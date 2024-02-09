# pal_rcon

Palworld 用の Rcon クライアントです。

> [!WARNING]
> サーバー側の実装の問題によりちゃんと動かないことがあります。

### 既知の問題

- マルチバイト文字に対応していない  
  サーバーがマルチバイト文字に対応していないため、マルチバイト文字が入っているといろいろとおかしくなる。  
  送信時: 文字化けを起こす  
  受信時: おそらく length がうまく計算されておらず、メッセージが途中で途切れてしまう

- ShowPlayers がうまく機能しない  
  うまく機能しない場合がいくつか確認しています。

  - プレイヤーがログイン中(キャラクリ中含む)の場合  
    ワールドに入る寸前に PlayerUID が読み込まれるので、それまでは PlayerUID が 00000000 となって Steam の名前が返される。  
    さらに Steam の名前がマルチバイト文字だと上記の不具合によりレスポンスが途中で切れてしまう。
  - プレイヤーの名前にマルチバイト文字が含まれている場合  
    上記参照。

- パケット ID がちゃんと返ってこない  
  Rcon では任意の数字を送信時に一緒に送ることで、レスポンスにその数字を含めて返してくれます。  
  ログイン時はちゃんと返ってきますが、コマンドを送信すると 0 が返ってきます。

### このクライアントの実装について

- "\n"で終わっていない場合は再試行する  
  PalWorld の レスポンスは必ず改行で終わるようです。  
  改行で終わっていない場合は max_attempts の数だけ再試行します。  
  特に起きやすい ShowPlayers ではデフォルトで 10 回にしてあります。  
  もし、マルチバイト文字が含まれていなければリトライの間にログインが完了し、正しい情報を取得できます。  
  最後まで"\n"で終わらなかった場合はうまくデコードできない可能性があるので IncompleteMessageError を送出します。  
  IncompleteMessageError.message に受信した Payload が入っています。

- 送信時のエンコードは ASCII です  
  UTF-8 でエンコードすると文字化けする上にレスポンスも文字化けしてしまうので ASCII でエンコードしています。  
  マルチバイト文字を渡すと UnicodeEncodeError となるので注意してください。

### 使い方

```
pip install pal_rcon
```

#### Sync

```python
from pal_rcon import PalRcon

# with Context Manager
with PalRcon("127.0.0.1", 25575, "password") as rcon:
    res = rcon.send_info()
    print(res.message)

# not Context Manager
rcon = PalRcon("127.0.0.1", 25575, "password")
rcon.connect()
res = rcon.send_info()
print(res.message)
rcon.disconnect()
```

#### Async

```python
from pal_rcon import AsyncPalRcon

# with Context Manager
async with AsyncPalRcon("127.0.0.1", 25575, "password") as rcon:
    res = await rcon.send_info()
    print(res.message)

# not Context Manager
rcon = AsyncPalRcon("127.0.0.1", 25575, "password")
await rcon.connect()
res = await rcon.send_info()
print(res.message)
await rcon.disconnect()
```

### Send Commands

```python
rcon.execute_command(command: str | list, max_attempts: int | None = 1) -> CommandResponse
rcon.send_shutdown(seconds: int | None = 1, message: str | None = "", send_save: bool | None = False, max_attempts: int | None = 1) -> CommandResponse:
rcon.send_do_exit(max_attempts: int | None = 1) -> CommandResponse
rcon.send_broadcast(message: str, max_attempts: int | None = 1) -> CommandResponse
rcon.send_kick_player(steam_id: str | int, max_attempts: int | None = 1) -> CommandResponse
rcon.send_ban_player(steam_id: str | int, max_attempts: int | None = 1) -> CommandResponse
rcon.send_show_players(max_attempts: int | None = 10) -> PlayerlistResponse
rcon.send_info(max_attempts: int | None = 1) -> CommandResponse
rcon.send_save(max_attempts: int | None = 1) -> CommandResponse
```

License MIT ©[Charahiro-tan](https://twitter.com/__Charahiro)
