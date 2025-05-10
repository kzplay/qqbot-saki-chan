import json
import re
from pathlib import Path
from textwrap import dedent

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent as Event, Message, MessageSegment
from nonebot.params import CommandArg
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from ..db.db import engine, create_db_and_tables
from ..db.models import User, Leaderboard
from src.plugins.gokz.core.kreedz import format_kzmode
from src.plugins.gokz.core.steam_user import convert_steamid

create_db_and_tables()


bind = on_command("bind", aliases={"绑定"})
mode = on_command("mode", aliases={"模式"})
test = on_command("test")
help_ = on_command('help', aliases={"帮助"})


@help_.handle()
async def _():
    image_path = Path('data/gokz/help.png')
    await help_.send(MessageSegment.image(image_path))


@bind.handle()
async def bind_steamid(bot: Bot, event: Event, args: Message = CommandArg()):
    if steamid := args.extract_plain_text():
        try:
            steamid = convert_steamid(steamid)
        except ValueError:
            return await bind.finish(MessageSegment.reply(event.message_id) + "Steamid格式不正确")
    else:
        return await bind.finish(MessageSegment.reply(event.message_id) + "请输steamid")

    # 阻止他们绑定前20玩家的steamid
    top20 = json.load(open("data/gokz/json/top20_players.json"))
    for player in top20:
        if steamid == player["steamid"]:
            return await bind.finish(MessageSegment.reply(event.message_id) + f"你是 {player['name']} 吗, 你就绑")

    with Session(engine) as session:
        rank: Leaderboard = session.get(Leaderboard, steamid)  # NOQA
        if not rank:
            return await bind.finish(MessageSegment.reply(event.message_id) + "用户不存在. 你至少上传过一次KZT的记录吗?")

    user_id = event.get_user_id()
    qq_info = await bot.call_api("get_stranger_info", user_id=user_id)
    qq_name = qq_info.get("nickname", 'Unknown')

    with Session(engine) as session:
        # 阻止重复绑定
        try:
            statement = select(User).where(User.steamid == steamid)
            exist_user: User = session.exec(statement).one()
            return await bind.finish(MessageSegment.reply(event.message_id) + f"该steamid已经被 {exist_user.name} QQ号{exist_user.qid} 绑定 ")
        except NoResultFound:
            pass

        user = session.get(User, user_id)
        if user:
            user.name = qq_name
            user.steamid = steamid
        else:
            user = User(qid=user_id, name=qq_name, steamid=steamid)
            session.add(user)
        session.commit()
        session.refresh(user)

    content = dedent(f"""
        绑定成功 {rank.name}!
        {user.steamid}
        请勿绑定他人的steamid, 否则可能会被拉黑
    """).strip()

    await bind.finish(MessageSegment.reply(event.message_id) + content)


@mode.handle()
async def update_mode(event: Event, args: Message = CommandArg()):
    if mode_ := args.extract_plain_text():
        try:
            mode_ = format_kzmode(mode_)  # Ensure this function validates and formats the mode correctly
        except ValueError:
            return await mode.finish(MessageSegment.reply(event.message_id) + "模式格式不正确")
    else:
        return await mode.finish(MessageSegment.reply(event.message_id) + "你模式都不给我我怎么帮你改ヽ(ー_ー)ノ")

    qid = event.get_user_id()
    with Session(engine) as session:
        user: User | None = session.get(User, qid)
        if not user:
            return await mode.finish(MessageSegment.reply(event.message_id) + "你还未绑定steamid")

        user.mode = mode_
        session.add(user)
        session.commit()
        session.refresh(user)

    await mode.finish(MessageSegment.reply(event.message_id) + f"模式已更新为: {mode_}")


@test.handle()
async def handle_first_receive(bot: Bot, event: Event, args: Message = CommandArg()):
    at_msg = event.get_message().copy()
    for segment in at_msg:
        if segment.type == 'at':
            return await bot.send(event, segment.data['qq'])

    mention_pattern = re.compile(r'\[CQ:at,qq=(\d+)\]')

    mentioned_users = mention_pattern.findall(args.extract_plain_text())

    if mentioned_users:
        for user_id in mentioned_users:
            await bot.send(event, f"Mentioned user ID: {user_id}")
    else:
        await bot.send(event, "No users mentioned.")
