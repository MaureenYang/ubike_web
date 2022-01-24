import requests
import json
import datetime, time
import os, sys
from db_conn import ubike_db
import pytz

if True:
    p = ubike_db()
    p.connect2db()

    if True:
        try:
            r = requests.get('https://tcgbusfs.blob.core.windows.net/blobyoubike/YouBikeTP.json')
            json_obj = json.loads(r.text)
            udata = json_obj['retVal']
            for idx in udata:
                try:
                    sdata = {}
                    sdata['sno'] = int(udata[idx]['sno'])
                    sdata['sbi'] = int(udata[idx]['sbi'])

                    dt = datetime.datetime.strptime(udata[idx]['mday'], "%Y%m%d%H%M%S").astimezone(pytz.timezone('US/Pacific'))
                    sdata['time'] = int(time.mktime(dt.timetuple()))
                    p.insert_ubike_data(sdata)
                except Exception as e:
                    print(e)


        except TimeoutError as e:
            print("[Youbike Timeouterror]")
            time.sleep(10)
        except Exception as e:
            print("[Youbike]Unexpected Error! ", e)
            time.sleep(10)

    p.dbclose()
