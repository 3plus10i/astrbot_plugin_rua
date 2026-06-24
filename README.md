# astrbot_plugin_rua

AstrBot 摸头插件 —— @机器人并发送 `rua`，即可生成摸头GIF动图。

## 功能

在群聊中 @机器人并发送以下指令：

| 指令 | 效果 |
|------|------|
| `rua`（全文）+ @ | 摸摸发送者的头像 |
| `rua我` / `rua一下` + @ | 摸摸发送者的头像 |
| `rua你` / `rua自己` + @ | 机器人摸自己的头像 |

同一 QQ 号 2 分钟内仅允许触发一次，超频回复提示。

**示例：**

```
用户：@AstrBot rua
机器人：[摸头GIF动图]

用户：@AstrBot rua你
机器人：[机器人摸自己头像的动图]
```

## 安装

将本插件放入 AstrBot 的插件目录 `data/plugins/astrbot_plugin_rua/` 即可。

## 依赖

- 基于 [UAPI 摸头GIF生成API](https://uapis.cn/docs/api-reference/get-image-motou) 生成动图
- 无需额外 Python 依赖

## 更新日志

详见 [CHANGELOG.md](./CHANGELOG.md)
