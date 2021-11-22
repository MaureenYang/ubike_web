import requests
import time
import threading, json
from queue import Queue
import datetime
import os, sys
import parser as pp
import backend as bk


ONE_MIN = 60
ONE_HOUR = ONE_MIN * 60
ONE_DAY = ONE_HOUR * 24


def GetUbikeDataThread():
    p = pp.ubike_db()
    p.connect2db()

    while True:
        try:
            r = requests.get('https://tcgbusfs.blob.core.windows.net/blobyoubike/YouBikeTP.json')
            json_obj = json.loads(r.text)
            udata = json_obj['retVal']
            for idx in udata:
                sdata = {}
                sdata['sno'] = int(udata[idx]['sno'])
                sdata['sbi'] = int(udata[idx]['sbi'])
                dt = datetime.datetime.strptime(udata[idx]['mday'], "%Y%m%d%H%M%S")
                sdata['time'] = int(time.mktime(dt.timetuple()))
                p.insert2_ubike_data(sdata)

            time.sleep(ONE_MIN)    #every minites

        except TimeoutError as e:
            print("[Youbike Timeouterror]")
            time.sleep(10)
        except:
            print("[Youbike]Unexpected Error!")
            time.sleep(10)


def GetWeatherThread():

    p = pp.weather_db()
    p.connect2db()

    ws0_req_str ='https://opendata.cwb.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=CWB-B74D517D-9F7C-44B9-90E9-4DF76361C725&format=JSON&stationId='
    ws1_req_str ='https://opendata.cwb.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWB-B74D517D-9F7C-44B9-90E9-4DF76361C725&format=JSON&stationId='

    ws0_list = ["466910" ,"466920","466930"]
    ws1_list = ["C0A980","C0A9E0","C0A9F0","C0AH40","C0AH70","C0AI40","C0AC40","C0AC70","C0AC80","C0A9C0"]

    while True:
        try:
            for ws in ws0_list:
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
                    dt = datetime.datetime.strptime(d['time'], "%Y-%m-%d %H:%M:%S")
                    d['time'] = int(time.mktime(dt.timetuple()))
                    p.insert_weather0_data(d)

            for ws in ws1_list:
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
                    dt = datetime.datetime.strptime(d['time'], "%Y-%m-%d %H:%M:%S")
                    d['time'] = int(time.mktime(dt.timetuple()))
                    p.insert_weather1_data(d)

            time.sleep(ONE_HOUR) #every hour

        except TimeoutError as e:
            # Maybe set up for a retry, or continue in a retry loop
            print("[Weather error]time out! try again")
            time.sleep(30)




if __name__ == "__main__":

    print ("Crawler Starting...")
    #create thread
    ubike_thread = threading.Thread(target = GetUbikeDataThread)
    weather_thread = threading.Thread(target = GetWeatherThread)


    ubike_thread.start()
    weather_thread.start()


    ubike_thread.join()
    weather_thread.join()


    print ("Crawler Finished")
