import os
from datetime import datetime


def check_last_modified_date(filepath):
    if os.path.exists(filepath):
        modified_time = os.path.getmtime(filepath)
        last_modified_date = datetime.fromtimestamp(modified_time)
        return last_modified_date
    else:
        return None
