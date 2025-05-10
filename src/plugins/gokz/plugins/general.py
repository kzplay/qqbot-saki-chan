import json
from pathlib import Path
from textwrap import dedent

from nonebot import on_command
from nonebot.adapters.qq import Bot, MessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from src.plugins.gokz.core.kreedz import format_kzmode
from src.plugins.gokz.core.steam_user import convert_steamid
from ..db.db import engine, create_db_and_tables
from ..db.models import User, Leaderboard

create_db_and_tables()


bind = on_command("bind", aliases={"绑定"})
mode = on_command("mode", aliases={"模式"})
test = on_command("test")
help_ = on_command('help', aliases={"帮助"})


@help_.handle()
async def _():
    image_path = Path('data/gokz/help.png')
    await help_.finish(MessageSegment.file_image(image_path))


@bind.handle()
async def bind_steamid(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if steamid := args.extract_plain_text():
        try:
            steamid = convert_steamid(steamid)
        except ValueError:
            return await bind.finish("Steamid格式不正确")
    else:
        return await bind.finish("请输steamid")

    # 阻止他们绑定前20玩家的steamid
    top20 = json.load(open("data/gokz/json/top20_players.json"))
    for player in top20:
        if steamid == player["steamid"]:
            return await bind.finish(f"你是 {player['name']} 吗, 你就绑")

    with Session(engine) as session:
        rank: Leaderboard = session.get(Leaderboard, steamid)  # NOQA
        if not rank:
            return await bind.finish("用户不存在. 你至少上传过一次KZT的记录吗?")

    user_id = event.get_user_id()
    qq_info = await bot.call_api("get_stranger_info", user_id=user_id)
    qq_name = qq_info.get("nickname", 'Unknown')

    with Session(engine) as session:
        # 阻止重复绑定
        try:
            statement = select(User).where(User.steamid == steamid)
            exist_user: User = session.exec(statement).one()
            return await bind.finish(f"该steamid已经被 {exist_user.name} QQ号{exist_user.qid} 绑定 ")
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

    await bind.finish(content)


@mode.handle()
async def update_mode(event: MessageEvent, args: Message = CommandArg()):
    if mode_ := args.extract_plain_text():
        try:
            mode_ = format_kzmode(mode_)
        except ValueError:
            return await mode.finish("模式格式不正确")
    else:
        return await mode.finish("你模式都不给我我怎么帮你改ヽ(ー_ー)ノ")

    qid = event.get_user_id()
    with Session(engine) as session:
        user: User | None = session.get(User, qid)
        if not user:
            return await mode.finish("你还未绑定steamid")

        user.mode = mode_
        session.add(user)
        session.commit()
        session.refresh(user)

    await mode.finish(f"模式已更新为: {mode_}")
