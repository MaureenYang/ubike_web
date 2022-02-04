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
            with open('YouBikeTP.json', 'w') as f:
                json.dump(json_obj, f)

            udata = json_obj['retVal']
            for idx in udata:
                try:
                    sdata = {}
                    sdata['sno'] = int(udata[idx]['sno'])
                    sdata['sbi'] = int(udata[idx]['sbi'])
                    dt = datetime.datetime.strptime(udata[idx]['mday'], "%Y%m%d%H%M%S").astimezone(pytz.timezone('Asia/Taipei'))
                    sdata['time'] = int(dt.timestamp())
                    ts = int(dt.timestamp())
                    p.insert_ubike_data(sdata)
                    p.delete_data_before_time(ts - 86400*7)

                except Exception as e:
                    print(e)


        except TimeoutError as e:
            print("[Youbike Timeouterror]")
            time.sleep(10)
        except Exception as e:
            print("[Youbike]Unexpected Error! ", e)
            time.sleep(10)

    p.dbclose()
