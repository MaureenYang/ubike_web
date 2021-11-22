import requests
import datetime, time
import sys,json
import pandas as pd
import sqlite3
from db_conn import ubike_db
from utility import data_preprocess
import pickle
import sklearn


wstation_01_req_str ='https://opendata.cwb.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=CWB-B74D517D-9F7C-44B9-90E9-4DF76361C725&format=JSON&stationId='
wstation_02_req_str ='https://opendata.cwb.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWB-B74D517D-9F7C-44B9-90E9-4DF76361C725&format=JSON&stationId='
#ubike_json_path = 'https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json'
ubike_json_path ='https://tcgbusfs.blob.core.windows.net/blobyoubike/YouBikeTP.json'

mapping_table = pd.read_csv("csv/mapping_table.csv")
mapping_table['sno'] = mapping_table['Unnamed: 0'].astype(int)
mapping_table = mapping_table.set_index(['sno']).drop(columns=['Unnamed: 0'])

p = ubike_db()

def get_key_value(src):
    new_element = {}
    key_name = src['elementName']
    try:
        new_element[key_name] = float(src['elementValue'])
    except:
        new_element[key_name] = src['elementValue']
    return new_element

def get_key_value_para(src):
    new_element = {}
    key_name = src['parameterName']
    try:
        new_element[key_name] = float(src['parameterValue'])
    except:
        new_element[key_name] = src['parameterValue']
    return new_element

def parse_weather_json(json_txt):
    w_dict = {}
    json_obj = json.loads(json_txt)
    kv = json_obj['records']['location'][0]['time']
    w_dict.update(kv)
    for k in json_obj['records']['location'][0]['weatherElement']:
        kv = get_key_value(k)
        w_dict.update(kv)
    return w_dict

#get weather by youbike station
def get_current_weather(sno):

    new_w = None
    w0 = 'w0'
    w1 = 'w1'
    station0 = ''
    station1 = ''
    try:
        ws = mapping_table[mapping_table.index==sno]

        station0 = ws['0'].values[0]
        station1 = ws['1'].values[0]

        if str(station0) == str(station1):
            r0 = requests.get(wstation_01_req_str + str(station0))
        else:
            r0 = requests.get(wstation_01_req_str + str(station1))
            r1 = requests.get(wstation_02_req_str + str(station0))

        w0 = parse_weather_json(r0.text)

        if str(station0) == str(station1):
            w1 = w0
        else:
            w1 = parse_weather_json(r1.text)

        new_w = {}
        new_w['UVI'] = w0['H_UVI']
        #new_w['Visb'] = w0['VIS']
        new_w['Describe'] = w0['Weather']
        new_w['WDIR'] = w1['WDIR']

        if str(station0) == str(station1):
            new_w['WDSE'] = w1['WDSD']
            new_w['H_24R'] = w1['24R']
        else:
            new_w['WDSE'] = w1['WDSD']
            new_w['H_24R'] = w1['H_24R']

        new_w['TEMP'] = w1['TEMP']
        new_w['HUMD'] = w1['HUMD']
        new_w['PRES'] = w1['PRES']

    except Exception as e:
        print('get_current_weather:',e)

    return new_w


def parse_ubike_json(json_txt,sno):
    json_obj = json.loads(json_txt)
    udata = json_obj['retVal']
    return udata[sno]


def get_station_info(sno):
    ubike_json = requests.get(ubike_json_path)
    return parse_ubike_json(ubike_json.text, sno)

def get_station_list():
    ubike_json = requests.get(ubike_json_path)
    json_obj = json.loads(ubike_json.text)
    udata = json_obj['retVal']
    station_list = []
    for idx in udata:
        station_list = station_list + [idx]
    return station_list

def get_all_station_list():
    station_list = []
    ubike_json = requests.get(ubike_json_path)
    json_obj = json.loads(ubike_json.text)
    udata = json_obj['retVal']
    for idx in udata:
        station_list = station_list + [udata[idx]]
    return station_list

def get_12h_historical_data(sno, current_ts,hour_before):
    ts = int(current_ts.timestamp())
    p.connect2db()
    h_data = p.get_historical_data(sno, ts + hour_before*(3600))
    p.dbclose()

    return h_data

def compose_predict_data(bdata, wdata):

    pred_dict = {}
    pred_dict['sbi'] = bdata[-1:].values[0]
    pred_dict['sbi_1h'] = bdata[-2:-1].values[0]
    pred_dict['time'] = bdata[-1:].index[0]
    for k in wdata:
        pred_dict[k] = wdata[k]

    return pred_dict

#need to fix
def predict_sbi(sno, current_ts):

    print('predict sno:', sno)
    a = None

    pred_col = ['sbi', 'hrs_0', 'hrs_1', 'hrs_10', 'hrs_11', 'hrs_12', 'hrs_13','hrs_14', 'hrs_15', 'hrs_16', 'hrs_17', 'hrs_18', 'hrs_19', 'hrs_2','hrs_20', 'hrs_21', 'hrs_22', 'hrs_23', 'hrs_3', 'hrs_4', 'hrs_5','hrs_6', 'hrs_7', 'hrs_8', 'hrs_9', 'HUMD', 'UVI']

    try:
        wdata = get_current_weather(sno)

        if wdata == None:
            return None

        bdata = get_12h_historical_data(sno, current_ts, 0)
        bdata_current = bdata[-2:]
        current_hr = current_ts.hour
        set_col_name = 'hrs_'+str(current_hr)
        pred_x = [bdata_current[-1:].values,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,wdata['HUMD'],wdata['UVI']]

        with open('pickle/model_ridge_sno_'+str(sno).zfill(4)+'.pickle', 'rb') as f:
            x = pickle.load(f)

        df = pd.DataFrame([pred_x], columns=pred_col)
        a = x.predict(df.values)[0][0]

        station_info = get_station_info(str(sno).zfill(4))
        tot = int(station_info['tot'])

        if a > tot:
            a = tot
        if a < 0:
            a = 0

        a = int(a)

    except Exception as e:
        print('predict_sbi:',e)

    return a


def get_weather_icon_path(wstr):

    flag1 = 0
    flag_rain = False
    flag_thunder = False
    return_str = ''

    if isinstance(wstr, str) == False:
        return 'sun.jpg'

    if wstr.find("晴")>= 0:
        flag1 = 1
    else:
        if wstr.find("多 雲") >= 0:
            flag1 = 2
        else:
            if wstr.find("陰")>= 0:
                flag1 = 3

    if wstr.find("雨")>= 0:
        flag_rain = True

    if wstr.find("雷")>= 0:
        flag_thunder = True

    if flag1 == 1:  #sun
        if flag_rain:
            if flag_thunder:
                return_str = 'rain_thunder.png'
            else:
                return_str = 'sun_rain.png'
        else:   #no rain
            return_str = 'sun.jpg'

    if flag1 == 2: #
        if flag_rain:
            if flag_thunder:
                return_str = 'rain_thunder.png'
            else:
                return_str = 'sun_cloudy_rain.png'
        else:   #no rain
            return_str = 'sun_cloudy.jpg'

    if flag1 == 3 or flag1 == 0:
        if flag_rain:
            if flag_thunder:
                return_str = 'rain_thunder.png'
            else:
                return_str = 'cloudy_rain.png'
        else:   #no rain
            return_str = 'cloudy.jpg'

    return 'weather_icon/'+return_str



if __name__ == "__main__":

    #print(predict_sbi(318,datetime.datetime.now()))
    '''
    for i in range(1,10):
        try:
            wd = get_current_weather(i)
            icon_path = get_weather_icon_path(wd['Describe'])
        except Exception as e:
            print(str(i) , ':', e)
    '''
    #print(get_current_weather(405))
    pass
