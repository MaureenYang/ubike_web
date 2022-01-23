import os,sys
import pandas as pd
import datetime, time
import sqlite3,json,requests
import psycopg2

ubike_db_file = 'E:/sqlite_db/crawler/ubike_db.db'
weather_db_file = 'E:/sqlite_db/crawler/weather_db.db'

POSTGRESQL_DB = True

class ubike_db():

    '''database'''
    conn = None

    def __init__(self):
        pass

    def connect2db(self):
        if POSTGRESQL_DB:
            self.conn = psycopg2.connect(database="dc6h7et50r2j0b", user="hpnfyuiogsmoac", password="a4463ccfee3a7e30666759a4d54e1bdd656e4f21553e693f72b69710abe781b1", host="ec2-52-204-72-14.compute-1.amazonaws.com", port="5432")
        else:
            self.conn = sqlite3.connect(ubike_db_file, check_same_thread=False)


    def insert_ubike_info(self, sinfo):
        self.connect2db()
        cmd = "INSERT INTO station_info (sno,sna,lat,lng,tot,sarea,ar,snaen,sareaen,aren) VALUES ({},'{}',{}, {},{},'{}','{}','{}','{}','{}');".format(int(sinfo['sno']), sinfo['sna'],float(sinfo['lat']), float(sinfo['lng']),int(sinfo['tot']),sinfo['sarea'],sinfo['ar'],sinfo['snaen'],sinfo['sareaen'],sinfo['aren'])
        print(cmd)
        c = self.conn.cursor()
        c.execute(cmd)
        self.conn.commit()
        self.dbclose()

    def insert_ubike_data(self,sdata):
        self.connect2db()
        cmd = "INSERT INTO ubike_data (sno,time,sbi) VALUES ({},{},{});".format(sdata['sno'],sdata['time'],sdata['sbi'])
        print(cmd)
        c = self.conn.cursor()
        c.execute(cmd)
        self.conn.commit()
        self.dbclose()

    def get_historical_data(self, sno, ts):
        self.connect2db()
        resample_h = None
        try:
            if ts%3600:
                ts = int(ts/3600 + 1)*3600
            else:
                ts = int(ts/3600)*3600

            h_data = []
            if POSTGRESQL_DB:
                cmd = "CREATE TEMP VIEW hist_data as SELECT * FROM ubike_data WHERE sno = {};".format(sno)
            else:
                cmd = "CREATE TEMP VIEW hist_data as SELECT * FROM ubike_data WHERE sno == {};".format(sno)
            c = self.conn.cursor()
            c.execute(cmd)
            self.conn.commit()
            start_time = ts
            cmd = "SELECT * from hist_data WHERE time > {} and time < {};".format(str(ts - 86400), str(ts))
            #cmd = "SELECT * from hist_data;"
            c = self.conn.cursor()
            if POSTGRESQL_DB:
                c.execute(cmd)
                rows = c.fetchall()
                for row in rows:
                    h_data = h_data + [row]
            else:
                for row in c.execute(cmd):
                    h_data = h_data + [row]
            self.dbclose()
            h_df = pd.DataFrame(h_data, columns=['sno','time','sbi'])
            h_df['time'] = h_df['time'].apply(lambda x : datetime.datetime.fromtimestamp(int(x)))
            h_df = h_df.set_index(pd.to_datetime(h_df['time']))
            h_df = h_df.drop(columns=['time'])
            resample_h = h_df.sbi.resample('H').mean().interpolate(method='linear').astype(int)

        except Exception as e:
            print(e)

        return resample_h

    def get_station_info(self):
        df = pd.DataFrame()
        try:
            h_data = []
            self.connect2db()
            cmd = "SELECT * from station_info "
            print(cmd)

            c = self.conn.cursor()
            if POSTGRESQL_DB:
                c.execute(cmd)
                rows = c.fetchall()
                for row in rows:
                    h_data = h_data + [row]
            else:
                for row in c.execute(cmd):
                    h_data = h_data + [row]

            self.dbclose()
            df = pd.DataFrame(h_data, columns=['sno', 'sname', 'lat', 'lng','tot','sarea','sar','snen','sareaen','saren'])
            df = df.set_index(df.sno)
        except Exception as e:
            print(e)

        return df

    def dbclose(self):
        self.conn.close()

class weather_db():
    '''database'''
    conn = None

    def __init__(self):
        pass

    def connect2db(self):
        if POSTGRESQL_DB:
            self.conn = psycopg2.connect(database="d3u983k86tsqp0", user="tllxvlxtjmfwmj", password="bc214f2e07b1eb845435d7c1dfda37314f26c885d21d22136cc58155566d862d", host="ec2-34-194-171-47.compute-1.amazonaws.com", port="5432")
        else:
            self.conn = sqlite3.connect(weather_db_file, check_same_thread=False)

    def insert_weather_info(self, winfo):
        self.connect2db()
        if POSTGRESQL_DB:
            cmd = "INSERT INTO station_info (stationId,locationName,lat,lon,city, city_sn,town,town_sn) VALUES ('{}','{}',{},{},'{}',{},'{}',{});".format(winfo['stationId'],winfo['locationName'],float(winfo['lat']),float(winfo['lon']),winfo['CITY'],int(winfo['CITY_SN']),winfo['TOWN'],int(winfo['TOWN_SN']))
        else:
            cmd = "INSERT INTO station_info (stationId,locationName,lat,lon,CITY, CITY_SN,TOWN,TOWN_SN) VALUES ('{}','{}',{},{},'{}',{},'{}',{});".format(winfo['stationId'],winfo['locationName'],float(winfo['lat']),float(winfo['lon']),winfo['CITY'],int(winfo['CITY_SN']),winfo['TOWN'],int(winfo['TOWN_SN']))

        #print(cmd)
        c = self.conn.cursor()
        c.execute(cmd)
        self.conn.commit()
        self.dbclose()

    def insert_weather0_data(self, winfo):
        self.connect2db()
        if POSTGRESQL_DB:
            cmd = "INSERT INTO weather_data (stationid,time,elev,wdir,wdsd,temp,humd,pres,h24r, uvi,vis, weather) VALUES ('{}',{},{},{},{},{},{},{},{},{},'{}','{}');".format(winfo['stationId'],int(winfo['time']),float(winfo['ELEV']),float(winfo['WDIR']),float(winfo['WDSD']),float(winfo['TEMP']),float(winfo['HUMD']),float(winfo['PRES']),float(winfo['24R']),float(winfo['H_UVI']),(winfo['VIS']),winfo['Weather'])
        else:
            cmd = "INSERT INTO weather_data (stationId,time,ELEV,WDIR,WDSD,TEMP,HUMD,PRES,H_24R, H_UVI,VIS, Weather) VALUES ('{}',{},{},{},{},{},{},{},{},{},'{}','{}');".format(winfo['stationId'],int(winfo['time']),float(winfo['ELEV']),float(winfo['WDIR']),float(winfo['WDSD']),float(winfo['TEMP']),float(winfo['HUMD']),float(winfo['PRES']),float(winfo['24R']),float(winfo['H_UVI']),(winfo['VIS']),winfo['Weather'])

        #print(cmd)
        c = self.conn.cursor()
        c.execute(cmd)
        self.conn.commit()
        self.dbclose()

    def insert_weather1_data(self, winfo):
        self.connect2db()
        if POSTGRESQL_DB:
            cmd = "INSERT INTO weather_data (stationid,time,elev,wdir,wdsd,temp,humd,pres,h24r) VALUES ('{}',{},{},{},{},{},{},{},{});".format(winfo['stationId'],int(winfo['time']),float(winfo['ELEV']),float(winfo['WDIR']),float(winfo['WDSD']),float(winfo['TEMP']),float(winfo['HUMD']),float(winfo['PRES']),float(winfo['H_24R']))
        else:
            cmd = "INSERT INTO weather_data (stationId,time,ELEV,WDIR,WDSD,TEMP,HUMD,PRES,H_24R) VALUES ('{}',{},{},{},{},{},{},{},{});".format(winfo['stationId'],int(winfo['time']),float(winfo['ELEV']),float(winfo['WDIR']),float(winfo['WDSD']),float(winfo['TEMP']),float(winfo['HUMD']),float(winfo['PRES']),float(winfo['H_24R']))

        print(cmd)
        c = self.conn.cursor()
        c.execute(cmd)
        self.conn.commit()
        self.dbclose()

    def get_historical_data(self, sno, ts):

        self.connect2db()
        h_df = None
        try:
            if ts%3600:
                ts = int(ts/3600 + 1)*3600
            else:
                ts = int(ts/3600)*3600

            h_data = []
            if POSTGRESQL_DB:
                cmd = "CREATE TEMP VIEW hist_data as SELECT * FROM weather_data WHERE stationid = \'{}\';".format(sno)
            else:
                cmd = "CREATE TEMP VIEW hist_data as SELECT * FROM weather_data WHERE stationId == \'{}\';".format(sno)
            #print(cmd)
            c = self.conn.cursor()
            c.execute(cmd)
            self.conn.commit()

            start_time = ts

            cmd = "SELECT * from hist_data WHERE time > {} and time < {};".format(str(ts - 86400), str(ts))
            #cmd = "SELECT * from hist_data;"

            if POSTGRESQL_DB:
                c.execute(cmd)
                rows = c.fetchall()
                for row in rows:
                    h_data = h_data + [row]
            else:
                c = self.conn.cursor()
                for row in c.execute(cmd):
                    h_data = h_data + [row]

            self.dbclose()
            #print(h_data)
            h_df = pd.DataFrame(h_data, columns=['stationId','time','ELEV','WDIR','WDSD','TEMP','HUMD','PRES','H_24R','H_UVI','Visb','Describe'])
            h_df['time'] = h_df['time'].apply(lambda x : datetime.datetime.fromtimestamp(int(x)))
            h_df = h_df.set_index(pd.to_datetime(h_df['time']))
            h_df = h_df.drop(columns=['time'])
            h_df.index = h_df.index.floor('H')

        except Exception as e:
            print(e)

        return h_df

    def dbclose(self):
        self.conn.close()

if __name__ == "__main__":

    p = weather_db()
    p.connect2db()
    ts = int(time.time())
    h_df = p.get_historical_data("466910", ts)
    print(h_df)

    p.dbclose()
