from datetime import datetime
import pytz
from flask import jsonify

def get_romania_time():
    """Get current time in Romania (only hours and minutes)"""
    romania_tz = pytz.timezone('Europe/Bucharest')
    current_time = datetime.now(romania_tz)
    return {
        'hour': current_time.hour,
        'minute': current_time.minute
    }
