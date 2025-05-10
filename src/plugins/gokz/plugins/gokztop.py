import math
from datetime import datetime
from textwrap import dedent

import aiohttp
import httpx
from nonebot import on_command, Bot, logger
from nonebot.adapters.onebot.v11 import MessageEvent as Event, Message, MessageSegment, GroupMessageEvent, \
    PrivateMessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .kzglobal import group_map_names, DEFAULT_MAP, private_map_names
from ..api.dataclasses import LeaderboardData
from ..api.helper import fetch_json
from src.plugins.gokz.core.command_helper import CommandData
from ..db.deps import SessionDep
from ..db.models import User
from src.plugins.gokz.core.formatter import format_gruntime, diff_seconds_to_time
from src.plugins.gokz.core.kreedz import search_map
from src.plugins.gokz.core.kz.records import count_servers
from src.plugins.gokz.core.steam_user import convert_steamid

BASE = "https://api.gokz.top/"

rank = on_command('rank', aliases={'排行'})
progress = on_command('mp', aliases={'progress', '进度'})
ccf = on_command('ccf', aliases={'查成分'})
pk = on_command('pk', aliases={'pk'})
find = on_command('find', aliases={'查找'})
group_rank = on_command('群排名', aliases={'group_rank'}, permission=SUPERUSER)


@group_rank.handle()
async def _(bot: Bot, session: SessionDep, event: GroupMessageEvent):
    logger.info("Writing member list")
    members = await bot.get_group_member_list(group_id=event.group_id)
    qid_list = [str(member['user_id']) for member in members]
    ranks = []
    for qid in qid_list:
        user = session.get(User, str(qid))
        if not user:
            print(f'user {qid} not found')
            continue
        url = f'{BASE}leaderboard/{user.steamid}?mode=kz_timer'
        try:
            rank_data = await fetch_json(url, timeout=10)
            # if rank_data.get('detail'):
            #     return await rank.finish(MessageSegment.reply(event.message_id) + rank_data.get('detail'))
            data = LeaderboardData.from_dict(rank_data)
            ranks.append(data)
        except Exception as e:
            print(str(e))
        # except AttributeError:
        #     return await rank.finish("获取数据失败，请稍后再试。")
        # except KeyError:
        #     return await rank.finish("无法解析排行榜数据，请稍后再试。")
    ranks.sort(key=lambda x: x.pts_skill if x.pts_skill is not None else -math.inf, reverse=True)
    content = ''
    for i, rank_ in enumerate(ranks, start=1):
        try:
            steamid64 = convert_steamid(rank_.steamid)
        except Exception as e:
            steamid64 = None
        content += f"{i}. {rank_.name} {rank_.pts_skill} {steamid64}\n"
    await group_rank.send(content)


@find.handle()
async def find_handle(event: Event, args: Message = CommandArg()):
    if name := args.extract_plain_text():
        players = await fetch_json(f"https://api.gokz.top/leaderboard/search/{name}?mode=kz_timer")
        players = [LeaderboardData.from_dict(player) for player in players]

        content = '════查找玩家════\n'
        if not players:
            content += "未找到该玩家"
        for player in players:
            content += f"{player.name} | {player.steamid} | {player.total_points//10000}w分\n"
        reply = MessageSegment.reply(event.message_id) + content
        await find.send(reply)
    else:
        await find.send(MessageSegment.reply(event.message_id) + "客服小祥提醒您: 请输入你要查找的玩家名")


@pk.handle()
async def pk_handle(bot: Bot, event: Event, args: Message = CommandArg()):
    cd = CommandData(event, args)
    if cd.error:
        return await bot.send(event, MessageSegment.reply(event.message_id) + cd.error)
    if not cd.steamid2:
        return await bot.send(event, MessageSegment.reply(event.message_id) + "未指定对手")

    # 未提供参数默认比较ank
    if not cd.args:
        try:
            rank1_data = await fetch_json(f'{BASE}leaderboard/{cd.steamid}?mode={cd.mode}')
            rank1 = LeaderboardData.from_dict(rank1_data)

            rank2_data = await fetch_json(f'{BASE}leaderboard/{cd.steamid2}?mode={cd.mode}')
            rank2 = LeaderboardData.from_dict(rank2_data)
        except aiohttp.ClientError:
            return await bot.send(event, "无法访问排行榜服务，请稍后再试。")
        except KeyError:
            return await bot.send(event, "无法解析排行榜数据，请稍后再试。")

        win = True if rank2.pts_skill > rank1.pts_skill else False

        table_content = dedent(
            f"""
            ╔═══╦════╦════╗
            ║玩家　║ {rank1.name} ║ {rank2.name} ║
            ╠═══╬════╬════╣
            ║Rating　║{'✅' if not win else '❌'} {rank1.pts_skill} ║ {'✅' if win else '❌'} {rank2.pts_skill} ║
            ║　段位　║{'✅' if not win else '❌'} {rank1.rank_name} ║ {'✅' if win else '❌'} {rank2.rank_name} ║
            ║　排名　║{'✅' if not win else '❌'} {rank1.rank} ║ {'✅' if win else '❌'} {rank2.rank} ║
            ║百分比　║{'✅' if not win else '❌'} {rank1.percentage} ║ {'✅' if win else '❌'} {rank2.percentage} ║
            ║　总分　║{'✅' if rank1.total_points > rank2.total_points else '❌'} {rank1.total_points//1000}k║ {'✅' if rank2.total_points > rank1.total_points else '❌'} {rank2.total_points//1000}k║
            ║地图数　║{'✅' if rank1.count > rank2.count else '❌'} {rank1.count} ║ {'✅' if rank2.count > rank1.count else '❌'} {rank2.count} ║
            ║平均分　║{'✅' if rank1.pts_avg > rank2.pts_avg else '❌'} {rank1.pts_avg} ║ {'✅' if rank2.pts_avg > rank1.pts_avg else '❌'} {rank2.pts_avg} ║
            ║裸跳均分║ {'✅' if rank1.pts_avg_pro > rank2.pts_avg_pro else '❌'} {rank1.pts_avg_pro} ║ {'✅' if rank2.pts_avg_pro > rank1.pts_avg_pro else '❌'} {rank2.pts_avg_pro} ║
            ║ 900+   ║ {'✅' if rank1.count_p900 > rank2.count_p900 else '❌'} {rank1.count_p900} ║ {'✅' if rank2.count_p900 > rank1.count_p900 else '❌'} {rank2.count_p900} ║
            ║ 800+   ║ {'✅' if rank1.count_p800 > rank2.count_p800 else '❌'} {rank1.count_p800} ║ {'✅' if rank2.count_p800 > rank1.count_p800 else '❌'} {rank2.count_p800} ║
            ║ T567　║ {'✅' if (rank1.count_t5 + rank1.count_t6 + rank1.count_t7) > (rank2.count_t5 + rank2.count_t6 + rank2.count_t7) else '❌'} {rank1.count_t5 + rank1.count_t6 + rank1.count_t7} ║ {'✅' if (rank2.count_t5 + rank2.count_t6 + rank2.count_t7) > (rank1.count_t5 + rank1.count_t6 + rank1.count_t7) else '❌'} {rank2.count_t5 + rank2.count_t6 + rank2.count_t7} ║
            ╚════╩════╩════╝
            """
        ).strip()

        # Send the rotated table as a message
        await bot.send(event, MessageSegment.reply(event.message_id) + table_content)

        if win:
            await bot.send(event, f"拜托，你真的很弱诶 {rank1.name} 😎")
        else:
            await bot.send(event, f"被 {rank1.name} 干趴下了 😢")

        return

    # deprecated
    # elif cd.args[0] == 'lj':
    #     return await bot.send(event, "WIP")
    # else:
    #     map_name = search_map(cd.args[0])[0]
    #     # tp records
    #     url1 = f'https://api.gokz.top/records/top/{cd.steamid}?mode={cd.mode}&map_name={map_name}&has_tp=true'
    #     url2 = f'https://api.gokz.top/records/top/{cd.steamid2}?mode={cd.mode}&map_name={map_name}&has_tp=true'
    #
    #     # pro records
    #     url3 = f'https://api.gokz.top/records/top/{cd.steamid}?mode={cd.mode}&map_name={map_name}&has_tp=false'
    #     url4 = f'https://api.gokz.top/records/top/{cd.steamid2}?mode={cd.mode}&map_name={map_name}&has_tp=false'
    #
    #     tp1, tp2, pro1, pro2 = await fetch_get(url1, url2, url3, url4)
    #
    #     tp1 = GlobalRecord(**tp1[0]) if tp1 else None
    #     tp2 = GlobalRecord(**tp2[0]) if tp2 else None
    #     pro1 = GlobalRecord(**pro1[0]) if pro1 else None
    #     pro2 = GlobalRecord(**pro2[0]) if pro2 else None
    #
    #     print(tp1, tp2, pro1, pro2, sep="\n")
    #
    #     content = "====".join([str(tp1), str(tp2), str(pro1), str(pro2)])
    #
    #     await pk.send(content)

    # await bot.send(event)
    return


@ccf.handle()
async def check_cheng_fen(event: Event, args: Message = CommandArg()):
    cd = CommandData(event, args)
    if cd.error:
        return await ccf.finish(cd.error)

    url = f'{BASE}records/top/{cd.steamid}?mode={cd.mode}'
    if cd.args:
        if cd.args[0] == 'all':
            url = f'{BASE}records/{cd.steamid}?mode={cd.mode}'

    records = await fetch_json(url)
    data = count_servers(records, limit=10)
    content = dedent(f"""
        ════成分查询════
        玩家:　　{records[0]['player_name']}
        steamid: {records[0]['steam_id']}
        模式:　　{cd.mode}
        ════════════
    """).strip() + '\n'
    for idx, server in enumerate(data):
        content += f"{idx+1}. {server['server']} | {server['count']}次 | ({server['per']}%)\n"
    return await ccf.finish(MessageSegment.reply(event.message_id) + content)


@rank.handle()
async def gokz_top_rank(event: Event, args: Message = CommandArg()):
    cd = CommandData(event, args)
    print(cd.update)
    if cd.error:
        return await rank.finish(MessageSegment.reply(event.message_id) + cd.error)

    if cd.update:
        httpx.put(f'http://localhost:8000/leaderboard/{cd.steamid}?mode={cd.mode}')

    url = f'{BASE}leaderboard/{cd.steamid}?mode={cd.mode}'
    logger.warning(f"querying {url} failed")
    try:
        rank_data = await fetch_json(url, timeout=10)
        if rank_data.get('detail'):
            return await rank.finish(MessageSegment.reply(event.message_id) + rank_data.get('detail'))
        data = LeaderboardData.from_dict(rank_data)
    except AttributeError:
        return await rank.finish("获取数据失败，请稍后再试。")
    except KeyError:
        return await rank.finish("无法解析排行榜数据，请稍后再试。")

    content = dedent(
        f"""     
        昵称:　　　{data.name}
        steamid:　 {data.steamid}
        模式:　　　{cd.mode}
        Rating:　　{data.pts_skill}
        段位:　　　{data.rank_name}
        排名:　　　No.{data.rank}
        百分比:　　{data.percentage}
        总分:　　　{data.total_points}
        地图数:　　{data.count}
        平均分:　　{data.pts_avg}
        常玩服务器:{data.most_played_server}
        上次更新:　{data.updated_on.replace('T', ' ')}
        """
    ).strip()
    return await rank.finish(MessageSegment.reply(event.message_id) + content)


@progress.handle()
async def map_progress(event: Event, args: Message = CommandArg()):
    cd = CommandData(event, args)
    if cd.error:
        return await progress.finish(cd.error)

    if not cd.args:
        if isinstance(event, GroupMessageEvent):
            map_name = group_map_names.get(event.group_id, DEFAULT_MAP)
        elif isinstance(event, PrivateMessageEvent):
            map_name = private_map_names.get(event.user_id, DEFAULT_MAP)
        else:
            map_name = DEFAULT_MAP
    else:
        map_name = search_map(cd.args[0])[0]
        if isinstance(event, GroupMessageEvent):
            group_map_names[event.group_id] = map_name
        elif isinstance(event, PrivateMessageEvent):
            private_map_names[event.user_id] = map_name

    query_url = (
        f"https://api.gokz.top/records/{cd.steamid}?mode={cd.mode}&map_name={map_name}"
    )
    data = await fetch_json(query_url)

    if not data:
        return await progress.finish(MessageSegment.reply(event.message_id) + f"你尚未完成过{map_name}")

    data.sort(key=lambda x: x['created_on'])
    records = []
    completions = []
    completions_counter = 0
    for record in data:
        if not records or record['time'] < records[-1]['time']:
            records.append(record)
            completions.append(completions_counter)
            completions_counter = 0
        else:
            completions_counter += 1

    records = list(reversed(records))
    completions = list(reversed(completions))

    tp_records = [record for record in records if record['teleports'] > 0]
    pro_records = [record for record in records if record['teleports'] == 0]

    content = f"玩家: {data[0]['player_name']}\n在地图: {data[0]['map_name']}\n模式: {data[0]['mode']} 的进度\n"

    def generate_content(records_, completions_, title):
        content_ = f"====={title}=====\n"
        for i, record_ in enumerate(records_):
            if i == len(records_) - 1:
                time_diff = 0
            else:
                time_diff = records_[i + 1]['time'] - record_['time']
            content_ += f"╔ {format_gruntime(record_['time'], True)} (-{diff_seconds_to_time(time_diff)})\n"
            content_ += f"╠ {record_['points']}分　　{record_['teleports']} TPs \n"
            content_ += f"╚ {datetime.strptime(record_['created_on'], '%Y-%m-%dT%H:%M:%S').strftime('%Y年%m月%d日 %H:%M')}\n"
            if i < len(records_) - 1 and completions_[i + 1] > 0:
                content_ += f"--- {completions_[i + 1]} 次完成 ---\n"
        return content_

    content += generate_content(tp_records, completions, 'TP')
    content += generate_content(pro_records, completions, 'PRO')
    await progress.finish(MessageSegment.reply(event.message_id) + content)
