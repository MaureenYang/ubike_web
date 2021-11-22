# -*- coding: utf-8 -*-
"""
Created on Sun Jul 18 08:54:42 2021

@author: Maureen
"""
import pandas as pd
import os, sys
import datetime as dt
import numpy as np
import math


def update_uvi_category(df):
    #UVI_val_catgory = {'>30': 8, '21-30':7, '16-20':6, '11-15':5,'7-10':4, '3-6':3, '1-2':2,'<1':1,'0':0}
    UVI_catgory = {'uvi_30': 8, 'uvi_20_30': 7, 'uvi_16_20': 6, 'uvi_11_16': 5, 'uvi_7_11': 4, 'uvi_3_7': 3, 'uvi_1_3': 2, 'uvi_1': 1, 'uvi_0': 0}
    uvi_c = pd.Series(index = df.index,data=[None for _ in range(len(df.index))])
    uvi_c[df.UVI > 30] = 'uvi_30'
    idx = (df.UVI > 20) & (df.UVI <= 30)
    uvi_c[idx] = 'uvi_20_30'
    idx = (df.UVI > 16) & (df.UVI <= 20)
    uvi_c[idx] = 'uvi_16_20'
    idx = (df.UVI > 11) & (df.UVI <= 16)
    uvi_c[idx] = 'uvi_11_16'
    idx = (df.UVI > 7) & (df.UVI <= 11)
    uvi_c[idx] = 'uvi_7_11'
    idx = (df.UVI > 3) & (df.UVI <= 7)
    uvi_c[idx] = 'uvi_3_7'
    idx = (df.UVI > 1) & (df.UVI <= 3)
    uvi_c[idx] = 'uvi_1_3'
    uvi_c[df.UVI <= 1] = 'uvi_1'
    uvi_c[df.UVI == 0] = 'uvi_0'

    uvi_c = uvi_c.map(UVI_catgory) #turning to label encoding
    df.UVI = uvi_c

    return df

def degToCompass(df):
    arr=["WD_N","WD_NNE","WD_NE","WD_ENE","WD_E","WD_ESE", "WD_SE", "WD_SSE","WD_S","WD_SSW","WD_SW","WD_WSW","WD_W","WD_WNW","WD_NW","WD_NNW"]
    idx = (((df.WDIR/22.5)+.5)% 16).astype(int)
    idx = idx.apply(lambda x: arr[x])
    df.WDIR = idx
    return df

def calComfortIndex(x):
    T = x[0]
    Td = x[1]
    level = None
    #thi_val = temp - 0.55*(1-(math.exp(17.269*td)/(td+237.3)-(17.269*temp)/(temp+237.3)))*(temp-14)
    thi_val = T-0.55*(1-(math.exp((17.269*Td)/(Td+237.3)) / math.exp((17.269*T)/(T+237.3))))*(T-14)

    if thi_val <= 10:
        level = 0#'ext_cold'

    if thi_val > 10 and thi_val <= 15:
        level = 1#"cold"

    if thi_val > 15 and thi_val <= 19:
        level = 2#"little_cold"

    if thi_val > 19 and thi_val <= 26:
        level = 3#"comfort"

    if thi_val > 26 and thi_val <= 30:
        level = 4#"hot"

    if thi_val > 30:
        level = 5#"ext_hot"

    return level

def addComfortIndex(df):
    df['comfort'] = df[['TEMP','td']].apply(lambda x: calComfortIndex(x),axis=1)
    return df

all_tag = ['time', 'sbi', 'station_id', 'tot', 'CloudA', 'GloblRad', 'PrecpHour',
       'SeaPres', 'UVI', 'Visb', 'WDGust', 'WSGust', 'td', 'HUMD', 'H_24R',
       'PRES', 'TEMP', 'WDIR', 'WDSE']

float_tag = ['HUMD','PRES', 'TEMP', 'WDIR', 'WDSE','H_24R', 'PrecpHour', 'UVI','td']
interpolate_tag = ['TEMP','WDIR','H_24R','PRES','HUMD','WDSE','td']
fillzero_tag = ['UVI']
one_hot_tag = ['WDIR','weekday','hours']
normalize_tag = ['HUMD','PRES', 'TEMP', 'WDSE']


def data_preprocess(df):
    try:
        df = update_uvi_category(df)

        #df['weekday'] = df.index.weekday.astype(str)
        #df.weekday = df.weekday.apply(lambda x: 'wkdy_' + x )
        df['hours'] = df.index.hour.astype(str)
        df.hours = df.hours.apply(lambda x: 'hrs_' + x )


        #one-hot encoding
        for tag in one_hot_tag:
            data_dum = pd.get_dummies(df[tag], sparse=True)
            end = pd.DataFrame(data_dum)
            df[end.columns] = end
            df = df.drop(columns=[tag])

        #normalization
        if normalize:
            print("normalized!")
            for tag in normalize_tag:
                df[tag] = (df[tag] - df[tag].min()) / (df[tag].max()-df[tag].min())


        from workalendar.asia import Taiwan
        cal = Taiwan()
        holidayidx = []

        for t in cal.holidays(2021):
            for h in range(0,24):
                dd = dt.datetime.combine(t[0], dt.datetime.min.time())
                date_str = (dd + dt.timedelta(hours=h)).strftime("%Y-%m-%d %H:%M:%S")
                holidayidx = holidayidx + [date_str]

        #df['holiday'] = df.index.isin(holidayidx)

    except Exception as e:
        print('ERROR:',e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

    return df
