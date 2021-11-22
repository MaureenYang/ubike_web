import os,sys
import pandas as pd
import datetime, time
import sqlite3,json,requests

ubike_db_file = 'db/ubike_db.db'
weather_db_file = 'db/weather_db.db'

class ubike_db():

    '''database'''
    conn = None

    def __init__(self):
        pass

    def connect2db(self):
        self.conn = sqlite3.connect(ubike_db_file)

    def insert_ubike_info(self, sinfo):
        cmd = "INSERT INTO station_info (sno,sna,lat,lng,tot,sarea,ar,snaen,sareaen,aren) VALUES ({},'{}',{}, {},{},'{}','{}','{}','{}','{}');".format(int(sinfo['sno']), sinfo['sna'],float(sinfo['lat']), float(sinfo['lng']),int(sinfo['tot']),sinfo['sarea'],sinfo['ar'],sinfo['snaen'],sinfo['sareaen'],sinfo['aren'])
        print(cmd)
        c = self.conn.cursor()
        c.execute(cmd)
        self.conn.commit()

    def insert_ubike_data(self,sdata):
        cmd = "INSERT INTO ubike_data (sno,time,sbi) VALUES ({},{},{});".format(sdata['sno'],sdata['time'],sdata['sbi'])
        print(cmd)
        c = self.conn.cursor()
        c.execute(cmd)
        self.conn.commit()

    def get_historical_data(self, sno, ts):

        resample_h = None
        try:
            if ts%3600:
                ts = int(ts/3600 + 1)*3600
            else:
                ts = int(ts/3600)*3600

            h_data = []
            cmd = "CREATE TEMP VIEW hist_data as SELECT * FROM ubike_data WHERE sno == {};".format(sno)
            c = self.conn.cursor()
            c.execute(cmd)
            self.conn.commit()
            start_time = ts
            cmd = "SELECT * from hist_data WHERE time > {} and time < {};".format(str(ts - 86400), str(ts))
            c = self.conn.cursor()
            for row in c.execute(cmd):
                h_data = h_data + [row]

            h_df = pd.DataFrame(h_data, columns=['sno','time','sbi'])
            h_df['time'] = h_df['time'].apply(lambda x : datetime.datetime.fromtimestamp(int(x)))
            h_df = h_df.set_index(pd.to_datetime(h_df['time']))
            h_df = h_df.drop(columns=['time'])
            resample_h = h_df.sbi.resample('H').mean().interpolate(method='linear').astype(int)

        except Exception as e:
            print(e)

        return resample_h

    def dbclose(self):
        self.conn.close()

class weather_db():
    '''database'''
    conn = None

    def __init__(self):
        pass

    def connect2db(self):
        self.conn = sqlite3.connect(weather_db_file)

    def insert_weather_info(self, winfo):
        cmd = "INSERT INTO station_info (stationId,locationName,lat,lon,CITY, CITY_SN,TOWN,TOWN_SN) VALUES ('{}','{}',{},{},'{}',{},'{}',{});".format(winfo['stationId'],winfo['locationName'],float(winfo['lat']),float(winfo['lon']),winfo['CITY'],int(winfo['CITY_SN']),winfo['TOWN'],int(winfo['TOWN_SN']))

        #print(cmd)
        c = self.conn.cursor()
        c.execute(cmd)
        self.conn.commit()

    def insert_weather0_data(self, winfo):
        cmd = "INSERT INTO weather_data (stationId,time,ELEV,WDIR,WDSD,TEMP,HUMD,PRES,H_24R, H_UVI,VIS, Weather) VALUES ('{}',{},{},{},{},{},{},{},{},{},'{}','{}');".format(winfo['stationId'],int(winfo['time']),float(winfo['ELEV']),float(winfo['WDIR']),float(winfo['WDSD']),float(winfo['TEMP']),float(winfo['HUMD']),float(winfo['PRES']),float(winfo['24R']),float(winfo['H_UVI']),(winfo['VIS']),winfo['Weather'])

        #print(cmd)
        c = self.conn.cursor()
        c.execute(cmd)
        self.conn.commit()

    def insert_weather1_data(self, winfo):
        cmd = "INSERT INTO weather_data (stationId,time,ELEV,WDIR,WDSD,TEMP,HUMD,PRES,H_24R) VALUES ('{}',{},{},{},{},{},{},{},{});".format(winfo['stationId'],int(winfo['time']),float(winfo['ELEV']),float(winfo['WDIR']),float(winfo['WDSD']),float(winfo['TEMP']),float(winfo['HUMD']),float(winfo['PRES']),float(winfo['H_24R']))

        print(cmd)
        c = self.conn.cursor()
        c.execute(cmd)
        self.conn.commit()

    def dbclose(self):
        self.conn.close()

if __name__ == "__main__":

    p = ubike_db()
    p.connect2db()
    ts = int(time.time())
    h_df = p.get_historical_data(70, ts)
    print(h_df)

    p.dbclose()
