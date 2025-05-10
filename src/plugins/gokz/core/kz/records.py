from typing import List, Dict


def count_servers(records: List[Dict], limit=5) -> List[Dict]:
    from collections import Counter

    server_counts = Counter(record['server_name'] for record in records)

    total_records = sum(server_counts.values())

    top_5_servers = server_counts.most_common(limit)

    result = []
    for server_name, count in top_5_servers:
        percentage = (count / total_records) * 100
        result.append({
            "server": server_name,
            "count": count,
            "per": round(percentage, 2)  # rounding to 2 decimal places
        })

    return result
