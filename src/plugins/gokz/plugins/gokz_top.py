from datetime import datetime
from textwrap import dedent

import httpx
from nonebot import on_command, logger
from nonebot.adapters.qq import MessageEvent as Event, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from src.plugins.gokz.core.command_helper import CommandData
from src.plugins.gokz.core.formatter import format_gruntime, diff_seconds_to_time
from src.plugins.gokz.core.kreedz import search_map
from src.plugins.gokz.core.kz.records import count_servers
from ..api.dataclasses import LeaderboardData
from ..api.helper import fetch_json

BASE = "https://api.gokz.top/"

rank = on_command('rank', aliases={'排行'})
progress = on_command('mp', aliases={'progress', '进度'})
ccf = on_command('ccf', aliases={'查成分'})
pk = on_command('pk', aliases={'pk'})
find = on_command('find', aliases={'查找'})
group_rank = on_command('群排名', aliases={'group_rank'}, permission=SUPERUSER)


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
        await find.send(content)
    else:
        await find.send("客服小祥提醒您: 请输入你要查找的玩家名")


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
    return await ccf.finish(content)


@rank.handle()
async def gokz_top_rank(event: Event, args: Message = CommandArg()):
    cd = CommandData(event, args)
    print(cd.update)
    if cd.error:
        return await rank.finish(cd.error)

    if cd.update:
        httpx.put(f'http://localhost:8000/leaderboard/{cd.steamid}?mode={cd.mode}')

    url = f'{BASE}leaderboard/{cd.steamid}?mode={cd.mode}'
    logger.warning(f"querying {url} failed")
    try:
        rank_data = await fetch_json(url, timeout=10)
        if rank_data.get('detail'):
            return await rank.finish(rank_data.get('detail'))
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
    return await rank.finish(content)


@progress.handle()
async def map_progress(event: Event, args: Message = CommandArg()):
    cd = CommandData(event, args)
    if cd.error:
        return await progress.finish(cd.error)

    map_name = search_map(cd.args[0])[0]

    query_url = (
        f"https://api.gokz.top/records/{cd.steamid}?mode={cd.mode}&map_name={map_name}"
    )
    data = await fetch_json(query_url)

    if not data:
        return await progress.finish(f"你尚未完成过{map_name}")

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
    await progress.finish(content)
