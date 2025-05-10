from dataclasses import dataclass


@dataclass
class LeaderboardData:
    steamid: str
    name: str
    pts_skill: float
    rank_name: str
    most_played_server: str
    avatar_hash: str
    total_points: int
    count: int
    pts_avg: int
    pts_avg_t5: int
    pts_avg_t6: int
    pts_avg_t7: int
    pts_avg_pro: int
    pts_avg_tp: int
    count_t5: int
    count_t6: int
    count_t7: int
    count_p1000_tp: int
    count_p1000_pro: int
    count_p900: int
    count_p800: int
    count_t567_p900: int
    count_t567_p800: int
    count_t567_pro: int
    count_pro: int
    count_tp: int
    updated_on: str
    rank: int
    percentage: str
    steamid64: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            steamid=data.get('steamid'),
            name=data.get('name'),
            pts_skill=data.get('pts_skill'),
            rank_name=data.get('rank_name'),
            most_played_server=data.get('most_played_server'),
            avatar_hash=data.get('avatar_hash'),
            total_points=data.get('total_points'),
            count=data.get('count'),
            pts_avg=data.get('pts_avg'),
            pts_avg_t5=data.get('pts_avg_t5'),
            pts_avg_t6=data.get('pts_avg_t6'),
            pts_avg_t7=data.get('pts_avg_t7'),
            pts_avg_pro=data.get('pts_avg_pro'),
            pts_avg_tp=data.get('pts_avg_tp'),
            count_t5=data.get('count_t5'),
            count_t6=data.get('count_t6'),
            count_t7=data.get('count_t7'),
            count_p1000_tp=data.get('count_p1000_tp'),
            count_p1000_pro=data.get('count_p1000_pro'),
            count_p900=data.get('count_p900'),
            count_p800=data.get('count_p800'),
            count_t567_p900=data.get('count_t567_p900'),
            count_t567_p800=data.get('count_t567_p800'),
            count_t567_pro=data.get('count_t567_pro'),
            count_pro=data.get('count_pro'),
            count_tp=data.get('count_tp'),
            updated_on=data.get('updated_on'),
            rank=data.get('rank'),
            percentage=data.get('percentage'),
            steamid64=data.get('steamid64')
        )
