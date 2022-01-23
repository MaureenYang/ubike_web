import numpy as np
import pandas as pd
from datetime import datetime
import threading
import matplotlib.pylab as plt
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima_model import ARIMA


#import arima
THREAD_NUM = 8
MA_results = [None] * THREAD_NUM


def HistroicalAverage(train_y, test_y):
    mean_of_train = np.mean(train_y)
    predict_y = np.full((len(test_y)), np.mean(train_y))
    RMSE = np.sqrt(mean_squared_error(predict_y, test_y))#, squared=False))
    return RMSE


def MA_thread(series,n,id):
    try:
        #print("Thread ",threading.get_ident(),",id:",id," start...")
        predict_y = []
        test_y = []
        for i in range(0, len(series) - n):
            predict_y = predict_y + [np.average(series[i:i + n])]
            test_y = test_y + [series[n + i:n + 1 + i]]

        RMSE = (mean_squared_error(predict_y, test_y))
        MA_results[id] = RMSE

    except Exception as e:
        print('error:', e)

def MovingAverage(y1, y2):

    n = 48
    series = y1.append(y2).y_bemp
    thread_list = []
    y1_n = y1[-n:]
    series2 = y1_n.append(y2).reset_index().drop(columns=['index']).y_bemp
    avg_len = int(len(series2)/THREAD_NUM)
    start_idx = 0
    end_idx = avg_len
    for i in range(THREAD_NUM):
        sub_series = series2[start_idx:end_idx]
        t = threading.Thread(target=MA_thread,args=(sub_series, n, i))  # 建立執行緒
        t.start()  # 執行
        thread_list = thread_list + [t]
        start_idx = end_idx - n
        if i != 7:
            end_idx = start_idx + avg_len + n
        else:
            end_idx = len(series)
    for t in thread_list:
        t.join()
    print('thread all join')

    RMSE = np.sqrt(sum(MA_results)/THREAD_NUM)

    return RMSE


import statsmodels.api as sm
from itertools import product                    # some useful functions
import pickle



ps = range(0, 4)
d=1
qs = range(0, 4)
Ps = range(1, 4)
D=1
Qs = range(0, 4)
s = 24 # season length is still 24
# creating list with all the possible combinations of parameters
parameters = product(ps, qs, Ps, Qs)
parameters_list = list(parameters)

def SARIMA(y1, y2):

    #order = (4,1,3)
    #sorder = (2,1,1,24)

    train_y = y1.y_bemp.head(100)
    test_y = y2.y_bemp.head(10)
    results = []
    best_aic = float("inf")
    for param in parameters_list:
        print('current parameter:',param)
        order = (param[0],d,param[1])
        sorder = (param[2],D,param[3],24)
        model = sm.tsa.statespace.SARIMAX(train_y, order=order, seasonal_order=sorder)
        model_fit = model.fit(disp=False, low_memory=True)

        aic = model_fit.aic
        # saving best model, AIC and parameters
        if aic < best_aic:
            best_model = model_fit
            best_aic = aic
            best_param = param
        results.append([param, model_fit.aic])

    result_table = pd.DataFrame(results)
    result_table.columns = ['parameters', 'aic']
    # sorting in ascending order, the lower AIC is - the better
    result_table = result_table.sort_values(by='aic', ascending=True).reset_index(drop=True)
    p, q, P, Q = result_table.parameters[0]


    print(best_model.summary())
    predict_y = best_model.forecast(steps=len(test_y), exog=test_y)
    RMSE = np.sqrt(mean_squared_error(predict_y, test_y))
    print('SARIMA RMSE:', RMSE)




    return RMSE
