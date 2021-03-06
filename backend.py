import requests
import datetime, time
import sys,json
import pandas as pd
import sqlite3
from db_conn import ubike_db, weather_db
from utility import data_preprocess, get_cno_by_tot
import pickle
import sklearn
import pytz


wstation_01_req_str ='https://opendata.cwb.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=CWB-B74D517D-9F7C-44B9-90E9-4DF76361C725&format=JSON&stationId='
wstation_02_req_str ='https://opendata.cwb.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWB-B74D517D-9F7C-44B9-90E9-4DF76361C725&format=JSON&stationId='
#ubike_json_path = 'https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json'
ubike_json_path ='https://tcgbusfs.blob.core.windows.net/blobyoubike/YouBikeTP.json'

mapping_table = pd.read_csv("csv/mapping_table.csv")
mapping_table['sno'] = mapping_table['Unnamed: 0'].astype(int)
mapping_table = mapping_table.set_index(['sno']).drop(columns=['Unnamed: 0'])
ws0_list = ["466910" ,"466920","466930"]
ws1_list = ["C0A980","C0A9E0","C0A9F0","C0AH40","C0AH70","C0AI40","C0AC40","C0AC70","C0AC80","C0A9C0"]


class backend():

    p = None
    pw = None
    cur_weather_data = None
    cur_ubike_data = None

    def __init__(self):
        self.p = ubike_db()
        self.pw = weather_db()

    def get_key_value(self, src):
        new_element = {}
        key_name = src['elementName']
        try:
            new_element[key_name] = float(src['elementValue'])
        except:
            new_element[key_name] = src['elementValue']
        return new_element

    def get_key_value_para(self, src):
        new_element = {}
        key_name = src['parameterName']
        try:
            new_element[key_name] = float(src['parameterValue'])
        except:
            new_element[key_name] = src['parameterValue']
        return new_element

    def parse_weather_json(self, json_txt):
        w_dict = {}
        json_obj = json.loads(json_txt)
        kv = json_obj['records']['location'][0]['time']
        w_dict.update(kv)
        for k in json_obj['records']['location'][0]['weatherElement']:
            kv = self.get_key_value(k)
            w_dict.update(kv)
        return w_dict

    def get_all_weather_data(self):

        with open('Weather.json') as json_file:
            wdata = json.load(json_file)

        wdict = {}
        for station in ws0_list:
            try:
                #r = requests.get(wstation_01_req_str + str(station))
                #w = self.parse_weather_json(r.text)
                w = wdata[str(station)]
                new_w = {}
                new_w['UVI'] = w['H_UVI']
                new_w['Describe'] = w['Weather']
                new_w['WDIR'] = w['WDIR']
                new_w['WDSE'] = w['WDSD']
                new_w['H_24R'] = w['24R']
                new_w['TEMP'] = w['TEMP']
                new_w['HUMD'] = w['HUMD']
                new_w['PRES'] = w['PRES']
                wdict[station] = new_w
            except Exception as e:
                print('save_all_weather_data: station error', station, e)

        for station in ws1_list:
            try:
                #r = requests.get(wstation_02_req_str + str(station))
                #w = self.parse_weather_json(r.text)
                w = wdata[str(station)]
                new_w = {}
                new_w['UVI'] = None
                new_w['Describe'] = None
                new_w['WDIR'] = w['WDIR']
                new_w['WDSE'] = w['WDSD']
                new_w['H_24R'] = w['H_24R']
                new_w['TEMP'] = w['TEMP']
                new_w['HUMD'] = w['HUMD']
                new_w['PRES'] = w['PRES']

                wdict[station] = new_w
            except Exception as e:

                print('save_all_weather_data: station error', station, e)

        self.cur_weather_data = wdict

    def get_all_ubike_data(self):
        data_dict = {}
        #r = requests.get(ubike_json_path)
        #json_obj = json.loads(r.text)
        with open('YouBikeTP.json') as json_file:
            json_obj = json.load(json_file)
        udata = json_obj['retVal']
        for sno in udata:
            try:
                sdata = udata[sno]
                data_dict[sdata['sno']] = sdata
            except Exception as e:
                print(e, sno)

        self.cur_ubike_data = data_dict

    #get weather by youbike station
    def get_current_weather(self, sno):

        new_w = None
        w0 = 'w0'
        w1 = 'w1'
        station0 = ''
        station1 = ''
        try:
            ws = mapping_table[mapping_table.index==sno]

            station0 = ws['0'].values[0]
            station1 = ws['1'].values[0]
            #print('station0:', station0)
            #print('station1:', station1)
            if str(station0) == str(station1):
                r0 = requests.get(wstation_01_req_str + str(station0))
            else:
                r0 = requests.get(wstation_01_req_str + str(station1))
                r1 = requests.get(wstation_02_req_str + str(station0))

            w0 = self.parse_weather_json(r0.text)
            #print('station0:', r0.text)

            if str(station0) == str(station1):
                w1 = w0
            else:
                w1 = self.parse_weather_json(r1.text)
                #print('station1:', r1.text)

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

    def get_current_weather_from_db(self, sno):
        new_w = None
        w0 = 'w0'
        w1 = 'w1'
        station0 = ''
        station1 = ''
        try:
            ws = mapping_table[mapping_table.index==sno]
            ts = int(time.time())
            station0 = ws['1'].values[0]
            station1 = ws['0'].values[0]
            #print('station0:', station0)
            #print('station1:', station1)
            if str(station0) == str(station1):
                w0 = self.pw.get_historical_data(str(station0), ts , True)
                w1 = w0
            else:
                w0 = self.pw.get_historical_data(str(station0), ts, True)
                w1 = self.pw.get_historical_data(str(station1), ts, True)
            #print('station1:', r1.text)
            if w0.empty and not w1.empty:
                w0 = w1
                print('w0.empty and not w1.empty')
            if w1.empty and not w0.empty:
                w1 = w0
                print('w1.empty and not w0.empty')

            new_w = {}
            if False:
                new_w['UVI'] = w0['H_UVI']
                new_w['Describe'] = w0['Describe']
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

            else: #float(w0['H_UVI'].values[0])

                new_w['UVI'] = float(w0['H_UVI'].values[0])
                new_w['Describe'] = w0['Describe'].values[0]
                new_w['WDIR'] = float(w1['WDIR'].values[0])

                if str(station0) == str(station1):
                    new_w['WDSE'] = float(w1['WDSD'].values[0])
                    new_w['H_24R'] = float(w1['H_24R'].values[0])
                else:
                    new_w['WDSE'] = float(w1['WDSD'].values[0])
                    new_w['H_24R'] = float(w1['H_24R'].values[0])

                new_w['TEMP'] = float(w1['TEMP'].values[0])
                new_w['HUMD'] = float(w1['HUMD'].values[0])
                new_w['PRES'] = float(w1['PRES'].values[0])

        except Exception as e:
            print('get_current_weather_from_db:',e)

        return new_w

    #get weather by youbike station
    def get_current_weather_from_file(self, sno):

        new_w = None
        w0 = 'w0'
        w1 = 'w1'
        station0 = ''
        station1 = ''
        if self.cur_weather_data == None:
            self.get_all_weather_data()
        try:
            ws = mapping_table[mapping_table.index==sno]

            station0 = ws['1'].values[0]
            station1 = ws['0'].values[0]

            if str(station0) == str(station1):
                w0 = self.cur_weather_data[str(station0)]
                w1 = w0
            else:
                w0 = self.cur_weather_data[str(station0)]
                try:
                    w1 = self.cur_weather_data[str(station1)]
                except:
                    w1 = w0

            new_w = {}
            new_w['UVI'] = w0['UVI']
            #new_w['Visb'] = w0['VIS']
            new_w['Describe'] = w0['Describe']
            new_w['WDIR'] = w1['WDIR']

            if str(station0) == str(station1):
                new_w['WDSE'] = w1['WDSE']
                new_w['H_24R'] = w1['H_24R']
            else:
                new_w['WDSE'] = w1['WDSE']
                new_w['H_24R'] = w1['H_24R']

            new_w['TEMP'] = w1['TEMP']
            new_w['HUMD'] = w1['HUMD']
            new_w['PRES'] = w1['PRES']

        except Exception as e:
            print('get_current_weather:',e)

        return new_w

    def get_current_weather_from_db_predict(self, sno):
        new_w = None
        w0 = 'w0'
        w1 = 'w1'
        station0 = ''
        station1 = ''
        try:
            ws = mapping_table[mapping_table.index==sno]
            ts = int(time.time())
            station0 = ws['0'].values[0]
            station1 = ws['1'].values[0]
            #print('station0:', station0)
            #print('station1:', station1)
            if str(station0) == str(station1):
                w0 = self.pw.get_historical_data(str(station0), ts, False)
                w1 = w0
            else:
                w0 = self.pw.get_historical_data(str(station0), ts, False)
                w1 = self.pw.get_historical_data(str(station1), ts, False)
            #print('station1:', r1.text)
            if w0.empty and not w1.empty:
                w0 = w1
            if w1.empty and not w0.empty:
                w1 = w0

            new_w = {}
            try:
                new_w['UVI'] = float(w0['H_UVI'].values[0])
            except Exception as e:
                print(e,'UVI', w0['H_UVI'].values[0])
                new_w['UVI'] = 0

            try:
                new_w['HUMD'] = float(w1['HUMD'].values[0])
            except Exception as e:
                print(e,'HUMD', w0['HUMD'].values[0])
                new_w['HUMD'] = 0

        except Exception as e:
            print('get_current_weather_from_db_predict:',e)

        return new_w

    def parse_ubike_dict(self, udata, sno):
        udict = {}
        try:
            station_info = udata[sno]
            udict['lat'] = float(station_info['lat'])
            udict['lng'] = float(station_info['lng'])
            udict['tot'] = int(station_info['tot'])
            udict['sbi'] = int(station_info['sbi'])
            udict['bemp'] = int(station_info['tot']) - int(station_info['sbi'])
            udict['sno'] = int(station_info['sno'])
            udict['sna'] = station_info['sna']
            udict['ar'] =  station_info['ar']
            udict['act'] =  station_info['act']
        except Exception as e:
            print('parse_ubike_dict error :', e)
        return udict

    def parse_ubike_json(self, json_txt,sno):
        udict = {}
        try:
            json_obj = json.loads(json_txt)
            udata = json_obj['retVal']
            station_info = udata[sno]
            udict['lat'] = float(station_info['lat'])
            udict['lng'] = float(station_info['lng'])
            udict['tot'] = int(station_info['tot'])
            udict['sbi'] = int(station_info['sbi'])
            udict['bemp'] = int(station_info['tot']) - int(station_info['sbi'])
            udict['sno'] = int(station_info['sno'])
            udict['sna'] = station_info['sna']
            udict['ar'] =  station_info['ar']
            udict['act'] =  station_info['act']
        except Exception as e:
            print('parse_ubike_json error :', e)

        return udict


    def get_station_info(self, sno):
        if False:
            ubike_json = requests.get(ubike_json_path)
            return self.parse_ubike_json(ubike_json.text, sno)
        else:
            if self.cur_ubike_data == None:
                self.get_all_ubike_data()
            return self.parse_ubike_dict(self.cur_ubike_data, sno)



    def get_station_list(self):
        if False:
            ubike_json = requests.get(ubike_json_path)
            json_obj = json.loads(ubike_json.text)
            udata = json_obj['retVal']
        else:
            if self.cur_ubike_data == None:
                self.get_all_ubike_data()
            udata = self.cur_ubike_data
        station_list = []
        for idx in udata:
            station_list = station_list + [idx]
        return station_list

    def get_all_station_list(self):
        if False:
            ubike_json = requests.get(ubike_json_path)
            json_obj = json.loads(ubike_json.text)
            udata = json_obj['retVal']
        else:
            if self.cur_ubike_data == None:
                self.get_all_ubike_data()
            udata = self.cur_ubike_data

        station_list = []
        for idx in udata:
            station_list = station_list + [udata[idx]]
        return station_list

    def get_12h_historical_data(self, sno, current_ts, hour_before):
        try:
            ts = int(current_ts.timestamp())
            print(ts)
            h_data = self.p.get_historical_data(sno, ts)# + hour_before*(3600))
            print(h_data)
            #fill data
            cur_floor_ts = current_ts.replace(minute=0,second=0)
            start_ts = cur_floor_ts - datetime.timedelta(hours=(23+24))
            print(start_ts, cur_floor_ts)
            if isinstance(h_data, pd.Series) :
                h_dates = pd.date_range(start=start_ts.strftime("%m-%d-%Y %H:%M:%S %z"),end=cur_floor_ts.strftime("%m-%d-%Y %H:%M:%S %z"), freq='H')
                h_data = h_data.reindex(h_dates,fill_value=0)

        except Exception as e:
            print('get_12h_historical_data:', e)
            h_data = None
        print(h_data)
        return h_data

    def compose_predict_data(self, bdata, wdata):

        pred_dict = {}
        pred_dict['sbi'] = bdata[-1:].values[0]
        pred_dict['sbi_1h'] = bdata[-2:-1].values[0]
        pred_dict['time'] = bdata[-1:].index[0]
        for k in wdata:
            pred_dict[k] = wdata[k]

        return pred_dict

    #need to fix
    def predict_sbi(self, sno, current_ts):
        wdata = None
        a = None
        pred_col = ['sbi', 'hrs_0', 'hrs_1', 'hrs_10', 'hrs_11', 'hrs_12', 'hrs_13','hrs_14', 'hrs_15', 'hrs_16', 'hrs_17', 'hrs_18', 'hrs_19', 'hrs_2','hrs_20', 'hrs_21', 'hrs_22', 'hrs_23', 'hrs_3', 'hrs_4', 'hrs_5','hrs_6', 'hrs_7', 'hrs_8', 'hrs_9', 'HUMD', 'H_UVI']
        try:
            start_time = time.time()
            try:
                #wdata = self.get_current_weather(sno)
                wdata = self.get_current_weather_from_db_predict(sno)
                print('get_current_weather time:',time.time() - start_time)
                start_time = time.time()
            except Exception as e:
                print('get_current_weather error:',e)
                wdata = self.get_current_weather_from_db(sno)

            if wdata == None:
                return None

            bdata = self.get_12h_historical_data(sno, current_ts, 0)
            print('get_12h_historical_data time:',time.time() - start_time)
            start_time = time.time()
            bdata_current = bdata[-2:]
            current_hr = current_ts.hour
            set_col_name = 'hrs_' + str(current_hr)
            pred_x = [bdata_current[-1:].values[0],0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,wdata['HUMD'],wdata['UVI']]

            station_info = self.get_station_info(str(sno).zfill(4))
            print('get_station_info time:',time.time() - start_time)
            start_time = time.time()
            tot = int(station_info['tot'])
            cno = get_cno_by_tot(tot)
            print('get_cno_by_tot time:',time.time() - start_time)
            start_time = time.time()
            with open('pickle/model_cno_'+str(cno).zfill(2)+'.pickle', 'rb') as f:
                x = pickle.load(f)
            print('pickle.load time:',time.time() - start_time)
            start_time = time.time()
            df = pd.DataFrame([pred_x], columns=pred_col)
            df[set_col_name] = 1
            #a = x.predict(df.values)[0][0]
            a = x.predict(df)
            print('predict time:',time.time() - start_time)
            start_time = time.time()
            if a > tot:
                a = tot

            if a < 0:
                a = 0

            a = int(a)

        except Exception as e:
            print('predict_sbi:',e)


        return a

    def predict_sbi_data(self, station_info, current_ts, wdata):
        start_time = time.time()
        a = None
        sno = station_info['sno']
        pred_col = ['sbi', 'hrs_0', 'hrs_1', 'hrs_10', 'hrs_11', 'hrs_12', 'hrs_13','hrs_14', 'hrs_15', 'hrs_16', 'hrs_17', 'hrs_18', 'hrs_19', 'hrs_2','hrs_20', 'hrs_21', 'hrs_22', 'hrs_23', 'hrs_3', 'hrs_4', 'hrs_5','hrs_6', 'hrs_7', 'hrs_8', 'hrs_9', 'HUMD', 'H_UVI']
        try:
            bdata = self.get_12h_historical_data(sno, current_ts, 0)
            #print('bdata:', bdata)
            bdata_current = bdata[-2:]
            current_hr = current_ts.hour
            set_col_name = 'hrs_' + str(current_hr)
            pred_x = [bdata_current[-1:].values[0],0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,wdata['HUMD'],wdata['UVI']]
            start_time = time.time()
            tot = station_info['tot']
            cno = get_cno_by_tot(tot)
            start_time = time.time()
            with open('pickle/model_cno_'+str(cno).zfill(2)+'.pickle', 'rb') as f:
                x = pickle.load(f)

            start_time = time.time()
            df = pd.DataFrame([pred_x], columns=pred_col)
            df[set_col_name] = 1
            a = x.predict(df)

            start_time = time.time()
            if a > tot:
                a = tot

            if a < 0:
                a = 0

            a = int(a)
            print('predict:', a)
            cur_floor_ts = current_ts.replace(minute=0,second=0, microsecond=0)
            start_ts = cur_floor_ts + datetime.timedelta(hours=1)

            pred_s = pd.Series({start_ts:a})
            bdata = bdata.append(pred_s)
            print('predict time:',time.time() - start_time)

        except Exception as e:
            print('predict_sbi_data:',e)


        return bdata

    def get_weather_icon_path(self, wstr):

        flag1 = 0
        flag_rain = False
        flag_thunder = False
        return_str = ''

        if isinstance(wstr, str) == False:
            return 'sun.jpg'

        if wstr.find("???")>= 0:
            flag1 = 1
        else:
            if wstr.find("??? ???") >= 0:
                flag1 = 2
            else:
                if wstr.find("???")>= 0:
                    flag1 = 3

        if wstr.find("???")>= 0:
            flag_rain = True

        if wstr.find("???")>= 0:
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
                    return_str = 'cloudy_rain.jpg'
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
    bk = backend()
    bk.get_all_ubike_data()
    w = bk.cur_ubike_data
    print(w)
    #for h in range(0, 1):
        #print('hour', h)
        #print(bk.predict_sbi(1, datetime.datetime.now() - datetime.timedelta(hours=h)))
    pass
