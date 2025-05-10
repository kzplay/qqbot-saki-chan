from typing import List, Dict


def count_servers(records: List[Dict], limit=5) -> List[Dict]:
    from collections import Counter

    # Count occurrences of each server_name
    server_counts = Counter(record['server_name'] for record in records)

    # Get the total number of records
    total_records = sum(server_counts.values())

    # Get the top 5 most played servers
    top_5_servers = server_counts.most_common(limit)

    # Prepare the result
    result = []
    for server_name, count in top_5_servers:
        percentage = (count / total_records) * 100
        result.append({
            "server": server_name,
            "count": count,
            "per": round(percentage, 2)  # rounding to 2 decimal places
        })

    return result
