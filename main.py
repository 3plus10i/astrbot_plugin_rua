from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import At
from astrbot.api import logger

@register("astrbot_plugin_rua", "3plus10i", "Rua摸头插件 - @机器人并发送rua即可生成摸头GIF", "1.0.0")
class RuaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        """监听消息，检测 @bot + rua 并返回摸头GIF"""
        message_str = event.message_str.strip().lower()
        if "rua" not in message_str:
            return

        bot_mentioned = any(
            isinstance(seg, At) and str(seg.qq) == str(event.message_obj.self_id)
            for seg in event.message_obj.message
        )
        if not bot_mentioned:
            return

        user_id = event.message_obj.sender.user_id
        image_url = f"https://uapis.cn/api/v1/image/motou?qq={user_id}"
        logger.info(f"Rua插件: 生成摸头GIF, user_id={user_id}")
        yield event.image_result(image_url)
