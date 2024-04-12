import pytz
from pytz import timezone

def datetimefilter(value, format='%I:%M:%S %p'):
    if value is None:
        return ''
    tz = pytz.timezone('US/Eastern') # timezone you want to convert to from UTC
    utc = pytz.timezone('UTC')  
    value_adj = utc.localize(value, is_dst=None).astimezone(pytz.utc)
    local_dt = value_adj.astimezone(tz)
    return local_dt.strftime(format)

