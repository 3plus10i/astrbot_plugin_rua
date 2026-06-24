import time
import tempfile
import os
import io
import aiohttp
from PIL import Image
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import At, Plain, Image as ImageComponent
from astrbot.api import logger

@register("astrbot_plugin_rua", "3plus10i", "Rua摸头插件 - 发送rua即可生成摸头GIF", "1.4.0")
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

    @staticmethod
    def _extract_image_url(event: AstrMessageEvent) -> str | None:
        """提取消息中的图片URL（直接发送或引用回复）"""
        # 直接发送的图片
        for seg in event.message_obj.message:
            if isinstance(seg, ImageComponent) and hasattr(seg, 'url') and seg.url:
                return seg.url

        # 引用/回复消息中的图片
        if hasattr(event.message_obj, 'reply') and event.message_obj.reply:
            reply_msg = event.message_obj.reply
            if hasattr(reply_msg, 'message'):
                for seg in reply_msg.message:
                    if isinstance(seg, ImageComponent) and hasattr(seg, 'url') and seg.url:
                        return seg.url

        return None

    async def _generate_image_rua(self, image_url: str) -> str | None:
        """下载图片 -> 中心裁剪正方形 -> 压缩110x110 -> 调用UAPI生成摸头GIF"""
        temp_input = None
        try:
            # 1. 下载原图
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        return None
                    raw_bytes = await resp.read()

            # 2. 中心裁剪正方形并缩放至 110x110
            img = Image.open(io.BytesIO(raw_bytes))
            w, h = img.size
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side))
            img = img.resize((110, 110), Image.LANCZOS)

            temp_input = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            img.save(temp_input, format='PNG')
            temp_input.close()
            input_path = temp_input.name

            # 3. 上传处理后的图片到 UAPI
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                with open(input_path, 'rb') as f:
                    data.add_field('file', f, content_type='image/png')
                    async with session.post(
                        'https://uapis.cn/api/v1/image/motou', data=data
                    ) as resp:
                        if resp.status == 200:
                            gif_bytes = await resp.read()
                            with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as out:
                                out.write(gif_bytes)
                                return out.name
        except Exception as e:
            logger.error(f"Rua插件: 图片rua生成失败 - {e}")
        finally:
            if temp_input:
                try:
                    os.unlink(temp_input.name)
                except OSError:
                    pass
        return None

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        """监听消息，检测 @bot + rua 并返回摸头GIF"""
        # 提取纯文本（过滤 At 组件），用于指令匹配
        plain_text = "".join(
            seg.text for seg in event.message_obj.message
            if isinstance(seg, Plain)
        ).strip().lower()

        is_group = hasattr(event.message_obj, 'group_id') and event.message_obj.group_id
        if is_group:
            bot_mentioned = any(
                isinstance(seg, At) and str(seg.qq) == str(event.message_obj.self_id)
                for seg in event.message_obj.message
            )
            if not bot_mentioned:
                return

        user_id = str(event.message_obj.sender.user_id)

        # ---- 图片 rua（最高优先级）----
        image_url = self._extract_image_url(event)
        if image_url:
            is_image_rua = (
                plain_text == "rua"
                or "rua这个" in plain_text
                or "rua这张图" in plain_text
                or "rua这个图" in plain_text
                or "rua图片" in plain_text
                or "rua它" in plain_text
                or "rua图" in plain_text
            )
            if is_image_rua:
                if not self._check_cooldown(user_id):
                    logger.info(f"Rua插件: 图片rua频率限制触发, user_id={user_id}")
                    yield event.plain_result("rua太快了，等会再rua吧")
                    return

                temp_path = await self._generate_image_rua(image_url)
                if temp_path:
                    logger.info(f"Rua插件: 图片rua成功, image_url={image_url}, user_id={user_id}")
                    yield event.image_result(temp_path)
                    try:
                        os.unlink(temp_path)
                    except OSError:
                        pass
                else:
                    yield event.plain_result("rua图片生成失败，请稍后再试")
                return

        # 其他群员 @ 检测（仅群聊）
        other_ats = []
        if is_group:
            other_ats = [
                str(seg.qq) for seg in event.message_obj.message
                if isinstance(seg, At) and str(seg.qq) != str(event.message_obj.self_id)
            ]

        # 匹配 rua 模式（基于纯文本，不含 @ 组件）
        is_other_rua = other_ats and (
            "rua他" in plain_text
            or "rua她" in plain_text
            or "rua它" in plain_text
            or "rua一下" in plain_text
            or plain_text == "rua"
        )
        is_self_rua = not is_other_rua and ("rua你" in plain_text or "rua自己" in plain_text)
        is_sender_rua = not is_other_rua and (
            plain_text == "rua"
            or "rua我" in plain_text
            or "rua一下" in plain_text
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

        image_url_get = f"https://uapis.cn/api/v1/image/motou?qq={target_qq}"
        logger.info(f"Rua插件: 生成摸头GIF, target_qq={target_qq}, user_id={user_id}")
        yield event.image_result(image_url_get)
