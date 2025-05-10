from dataclasses import dataclass
from datetime import datetime


@dataclass
class GlobalRecord:
    id: int
    player_name: str
    steam_id: str
    server_id: int
    map_id: int
    stage: int
    mode: str
    time: float
    teleports: int
    created_on: datetime
    server_name: str
    map_name: str
    tier: int
    points: int


def separate_records(records: list[GlobalRecord]) -> tuple[list[GlobalRecord], list[GlobalRecord]]:
    tp = []
    pro = []
    for record in records:
        if record.teleports > 0:
            tp.append(record)
        else:
            pro.append(record)
    return tp, pro

