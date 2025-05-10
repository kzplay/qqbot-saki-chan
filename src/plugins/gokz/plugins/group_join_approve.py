import asyncio
import re
from json import JSONDecodeError

import httpx
import nonebot
from nonebot import on_request
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import GroupRequestEvent
from nonebot.adapters.onebot.v11.message import MessageSegment

from ..db.deps import SessionDep
from ..db.models import User
from src.plugins.gokz.core.steam_user import convert_steamid

join_group = on_request(
    priority=1,
    block=True
)


async def check_comment(comment):
    bot = nonebot.get_bot()
    url = f'https://api.gokz.top/leaderboard/{comment}?mode=kz_timer'
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        try:
            resp = resp.json()
        except JSONDecodeError:
            return False
        if len(resp) == 0:
            return False
        else:
            return resp.get('name', False)


@join_group.handle()
async def _grh(bot: Bot, event: GroupRequestEvent, session: SessionDep):
    if event.sub_type == 'add':
        user = session.get(User, event.user_id)
        if user:
            await event.approve(bot)

        comment = event.comment.strip()
        steamid = re.findall(re.compile('答案：(.*)'), comment)[0].strip()
        try:
            steamid = convert_steamid(steamid)
        except ValueError:
            reason = f'Steamid格式不正确'
            await join_group.send(f'{event.user_id} 申请入群失败')
            await event.reject(bot, reason=reason)

        if steamid != "":
            steam_name = await check_comment(steamid)
            if steam_name is False:
                reason = f'steamid: {steamid} 认证错误，未找到该steamid的玩家，请检查steamid是否正确，或是否至少上传过一张kzt全球记录'
                # await event.reject(bot, reason=reason)
                await join_group.send(f'{event.user_id} 入群申请失败\n{reason}')
                await join_group.send(f'/kz -s {steamid}')
            else:
                await event.approve(bot)
                await asyncio.sleep(2)
                await bot.set_group_card(group_id=event.group_id, user_id=event.user_id, card=steam_name)
                await join_group.send(MessageSegment.at(event.user_id) + f'欢迎 {steam_name} 加入本群\nsteamid: {steamid}')
                await join_group.send(f'/kz -s {steamid}')
        else:
            reason = f'steamid: {steamid} 认证错误，请输入steamid'
            await event.reject(bot, reason=reason)
            await join_group.finish(f'{event.user_id} 入群申请失败\n{reason}')
