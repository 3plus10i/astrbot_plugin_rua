import time
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import At
from astrbot.api import logger

@register("astrbot_plugin_rua", "3plus10i", "Rua摸头插件 - 发送rua即可生成摸头GIF", "1.3.0")
class RuaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self._last_rua: dict[str, float] = {}
        self._cooldown = 120  # 秒

    def _check_cooldown(self, user_id: str) -> bool:
        now = time.time()
        last = self._last_rua.get(user_id, 0)
        if now - last < self._cooldown:
            return False
        self._last_rua[user_id] = now
        return True

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        """监听消息，检测 @bot + rua 并返回摸头GIF"""
        message_str = event.message_str.strip().lower()

        is_group = hasattr(event.message_obj, 'group_id') and event.message_obj.group_id
        if is_group:
            bot_mentioned = any(
                isinstance(seg, At) and str(seg.qq) == str(event.message_obj.self_id)
                for seg in event.message_obj.message
            )
            if not bot_mentioned:
                return

        user_id = str(event.message_obj.sender.user_id)

        # 其他群员 @ 检测（仅群聊）
        other_ats = []
        if is_group:
            other_ats = [
                str(seg.qq) for seg in event.message_obj.message
                if isinstance(seg, At) and str(seg.qq) != str(event.message_obj.self_id)
            ]

        # 匹配 rua 模式
        is_other_rua = other_ats and (
            "rua他" in message_str
            or "rua她" in message_str
            or "rua它" in message_str
            or "rua一下" in message_str
            or message_str == "rua"
        )
        is_self_rua = not is_other_rua and ("rua你" in message_str or "rua自己" in message_str)
        is_sender_rua = not is_other_rua and (
            message_str == "rua"
            or "rua我" in message_str
            or "rua一下" in message_str
        )

        if not is_other_rua and not is_self_rua and not is_sender_rua:
            return

        # 频率限制（记录到发言人）
        if not self._check_cooldown(user_id):
            logger.info(f"Rua插件: 频率限制触发, user_id={user_id}")
            yield event.plain_result("rua太快了，等会再rua吧")
            return

        if is_other_rua:
            target_qq = other_ats[0]
        elif is_self_rua:
            target_qq = str(event.message_obj.self_id)
        else:
            target_qq = user_id

        image_url = f"https://uapis.cn/api/v1/image/motou?qq={target_qq}"
        logger.info(f"Rua插件: 生成摸头GIF, target_qq={target_qq}, user_id={user_id}")
        yield event.image_result(image_url)
