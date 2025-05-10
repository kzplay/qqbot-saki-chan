from datetime import datetime, timedelta


def format_gruntime(total_seconds, use_colon=False):
    # Calculate hours, minutes, seconds, and milliseconds
    hours = int(total_seconds // 3600)
    remaining_seconds = total_seconds % 3600
    minutes = int(remaining_seconds // 60)
    seconds = int(remaining_seconds % 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)

    # Format the result with leading zeros for minutes if more than 1 hour
    formatted_time = ""
    if use_colon:
        if hours > 0:
            formatted_time += f"{hours}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        else:
            formatted_time += f"{minutes}:{seconds:02d}.{milliseconds:03d}"
    else:
        if hours > 0:
            formatted_time += f"{hours}时"
            formatted_time += f"{minutes:02d}分{seconds:02d}秒{milliseconds:03d}"
        else:
            formatted_time += f"{minutes}分{seconds:02d}秒{milliseconds:03d}"

    return formatted_time


def record_format_time(time_str):
    dt = datetime.fromisoformat(time_str)

    offset = timedelta(hours=8)
    dt += offset

    # 格式化时间为指定格式
    formatted_time = dt.strftime("%Y年%-m月%-d日 %H:%M")

    return formatted_time


def diff_seconds_to_time(diff_sec):
    hours = int(diff_sec // 3600)
    remaining_seconds = diff_sec % 3600
    minutes = int(remaining_seconds // 60)
    seconds = int(remaining_seconds % 60)
    milliseconds = int((diff_sec - int(diff_sec)) * 1000)

    formatted_time = ""
    if hours > 0:
        formatted_time += f"{hours}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    elif minutes > 0:
        formatted_time += f"{minutes}:{seconds:02d}.{milliseconds:03d}"
    else:
        formatted_time += f"{seconds:02d}.{milliseconds:03d}"
    return formatted_time