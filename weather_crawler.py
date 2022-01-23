import requests
import json
import datetime, time
import os, sys
import backend
from db_conn import weather_db
import pytz

if True:

    p = weather_db()
    p.connect2db()
    bk = backend.backend()

    ws0_req_str ='https://opendata.cwb.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=CWB-B74D517D-9F7C-44B9-90E9-4DF76361C725&format=JSON&stationId='
    ws1_req_str ='https://opendata.cwb.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWB-B74D517D-9F7C-44B9-90E9-4DF76361C725&format=JSON&stationId='

    ws0_list = ["466910" ,"466920","466930"]
    ws1_list = ["C0A980","C0A9E0","C0A9F0","C0AH40","C0AH70","C0AI40","C0AC40","C0AC70","C0AC80","C0A9C0"]

    if True:
        try:
            for ws in ws0_list:
                try:
                    r0 = requests.get(ws0_req_str + ws)
                    json_obj = json.loads(r0.text)
                    for d in json_obj['records']['location']:
                        d.pop('lat')
                        d.pop('lon')
                        d.pop('locationName')
                        d.pop('parameter')
                        for k in d['weatherElement']:
                            kv = bk.get_key_value(k)
                            d.update(kv)
                        d.pop('weatherElement')
                        d['time'] = d['time']['obsTime']
                        dt = datetime.datetime.strptime(d['time'], "%Y-%m-%d %H:%M:%S").astimezone(pytz.timezone('Asia/Taipei'))
                        d['time'] = int(time.mktime(dt.timetuple()))
                        p.insert_weather0_data(d)
                except Exception as e:
                        print(e)

            for ws in ws1_list:
                try:
                    r0 = requests.get(ws1_req_str + ws)
                    json_obj = json.loads(r0.text)
                    for d in json_obj['records']['location']:
                        d.pop('lat')
                        d.pop('lon')
                        d.pop('locationName')
                        d.pop('parameter')
                        for k in d['weatherElement']:
                            kv = bk.get_key_value(k)
                            d.update(kv)
                        d.pop('weatherElement')
                        d['time'] = d['time']['obsTime']
                        dt = datetime.datetime.strptime(d['time'], "%Y-%m-%d %H:%M:%S").astimezone(pytz.timezone('Asia/Taipei'))
                        d['time'] = int(time.mktime(dt.timetuple()))
                        p.insert_weather1_data(d)
                except Exception as e:
                    print(e)

        except TimeoutError as e:
            # Maybe set up for a retry, or continue in a retry loop
            print("[Weather error]time out! try again")
            time.sleep(30)
        except Exception as e:
            print("[Weather] Unexpected Error! ", e)
            time.sleep(10)

    p.dbclose()
