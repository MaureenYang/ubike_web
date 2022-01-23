import sys
import sklearn
import pickle
import datetime
import pandas as pd
from utility import get_cno_by_tot, station_dict


sys.path.append('model/')
from sklearn.linear_model import Lasso
from db_conn import ubike_db, weather_db
from ridge_model import ridge

mapping_table = pd.read_csv("E:/sqlite_db/ubike_web/csv/mapping_table.csv")
mapping_table['sno'] = mapping_table['Unnamed: 0'].astype(int)
mapping_table = mapping_table.set_index(['sno']).drop(columns=['Unnamed: 0'])

p = ubike_db()
w = weather_db()
pred_col = ['sbi', 'hrs_0', 'hrs_1', 'hrs_10', 'hrs_11', 'hrs_12', 'hrs_13','hrs_14', 'hrs_15', 'hrs_16', 'hrs_17', 'hrs_18', 'hrs_19', 'hrs_2','hrs_20', 'hrs_21', 'hrs_22', 'hrs_23', 'hrs_3', 'hrs_4', 'hrs_5','hrs_6', 'hrs_7', 'hrs_8', 'hrs_9', 'HUMD', 'H_UVI']
ignore_list = [15, 20, 160, 198, 199, 200] # no station


station_sno_list = list(set(range(1,406)) - set(ignore_list))
for sno in []:#station_sno_list:
    try:
        ws = mapping_table[mapping_table.index==sno]
        station0 = ws['0'].values[0] #UVI
        station1 = ws['1'].values[0] #HUMD

        # read data from database:
        ts = datetime.datetime.now()
        ts = ts.replace(hour=0, second=0, minute=0)
        ts = int(ts.timestamp())
        wdata0 = w.get_historical_data(station0, ts)
        wdata1 = w.get_historical_data(station1, ts)
        bdata = p.get_historical_data(sno, ts)
        #print(wdata0)
        #print(wdata1)
        wdata0_m = wdata0[['WDIR','WDSD','TEMP','HUMD','PRES','H_24R']]
        wdata1_m = wdata1[['H_UVI','Visb','Describe']]
        wdata = pd.merge(wdata0_m, wdata1_m ,how='outer',left_index=True, right_index=True)
        for t in ['WDIR','WDSD','TEMP','HUMD','PRES','H_24R']:
            chk_dict= wdata1[t].to_dict()
            wdata[t] = wdata[t].fillna(value=chk_dict)
        #print(wdata)
        train_data = pd.merge(bdata, wdata ,how='outer',left_index=True, right_index=True)
        #print(train_data)
        train_data = train_data[['sbi','HUMD','H_UVI']]
        pred = pd.DataFrame(train_data,columns=pred_col).fillna(0)
        for index,row in pred.iterrows():
            tag = 'hrs_'+str(index.hour)
            pred.loc[index.strftime('%Y-%m-%d %H:%M:%S'), tag] = 1

        pred_x = pred[pred_col]
        pred_y = pred[['sbi']]


        try:
        #process data
            with open('E:/sqlite_db/ubike_web/pickle/model_ridge_sno_'+str(sno).zfill(4)+'.pickle', 'rb') as f:
                model = pickle.load(f)
            #    print(model.get_params())

            model.fit(pred_x,pred_y)
            #print(model.get_params())
            with open('E:/sqlite_db/ubike_web/pickle/model_ridge_sno_'+str(sno).zfill(4)+'.pickle', 'wb') as f:
                pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)
        except:
            print('sno:', sno, 'pickle missing')

    except Exception as e:
        print('err:', sno, ', ',e)


def trainer_sno():
    for sno in station_sno_list:
        print('sno:', sno)
        try:
            ws = mapping_table[mapping_table.index==sno]
            station0 = ws['0'].values[0] #UVI
            station1 = ws['1'].values[0] #HUMD

            # read data from database:
            ts = datetime.datetime.now()
            ts = ts.replace(hour=0, second=0, minute=0)
            ts = int(ts.timestamp())
            wdata0 = w.get_historical_data(station0, ts)
            wdata1 = w.get_historical_data(station1, ts)
            bdata = p.get_historical_data(sno, ts)

            wdata0_m = wdata0[['WDIR','WDSD','TEMP','HUMD','PRES','H_24R']]
            wdata1_m = wdata1[['H_UVI','Visb','Describe']]
            wdata = pd.merge(wdata0_m, wdata1_m ,how='outer',left_index=True, right_index=True)


            for t in ['WDIR','WDSD','TEMP','HUMD','PRES','H_24R']:
                chk_dict= wdata1[t].to_dict()
                wdata[t] = wdata[t].fillna(value=chk_dict)

            train_data = pd.merge(bdata, wdata ,how='outer',left_index=True, right_index=True)
            train_data = train_data[['sbi','HUMD','H_UVI']]
            pred = pd.DataFrame(train_data,columns=pred_col).fillna(0)
            for index,row in pred.iterrows():
                tag = 'hrs_'+str(index.hour)
                pred.loc[index.strftime('%Y-%m-%d %H:%M:%S'), tag] = 1

            pred_x = pred[pred_col]
            pred_y = pred[['sbi']]
            ret = ridge(pred_x,pred_y)
            model = ret[0]
            try:
                print('model', model)
            #process data
                if True:
                    with open('E:/sqlite_db/ubike_web/pickle/model_ridge_sno_'+str(sno).zfill(4)+'.pickle', 'rb') as f:
                        model = pickle.load(f)
                        print(model.get_params())

                    model.fit(pred_x,pred_y)
                    print(model.get_params())
                with open('E:/sqlite_db/ubike_web/pickle/model_ridge_sno_'+str(sno).zfill(4)+'.pickle', 'wb') as f:
                    pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)

            except:
                print('sno:', sno, 'pickle missing')

        except Exception as e:
            print('err:', sno, ', ',e)



def trainer_cno():
    for sno in station_sno_list:
        print('sno:', sno)
        try:
            ws = mapping_table[mapping_table.index==sno]
            station0 = ws['0'].values[0] #UVI
            station1 = ws['1'].values[0] #HUMD

            # read data from database:
            ts = datetime.datetime.now()
            ts = ts.replace(hour=0, second=0, minute=0)
            ts = int(ts.timestamp())
            wdata0 = w.get_historical_data(station0, ts)
            wdata1 = w.get_historical_data(station1, ts)
            bdata = p.get_historical_data(sno, ts)

            wdata0_m = wdata0[['WDIR','WDSD','TEMP','HUMD','PRES','H_24R']]
            wdata1_m = wdata1[['H_UVI','Visb','Describe']]
            wdata = pd.merge(wdata0_m, wdata1_m ,how='outer',left_index=True, right_index=True)

            for t in ['WDIR','WDSD','TEMP','HUMD','PRES','H_24R']:
                chk_dict= wdata1[t].to_dict()
                wdata[t] = wdata[t].fillna(value=chk_dict)

            train_data = pd.merge(bdata, wdata ,how='outer',left_index=True, right_index=True)
            train_data = train_data[['sbi','HUMD','H_UVI']]
            pred = pd.DataFrame(train_data,columns=pred_col).fillna(0)
            for index,row in pred.iterrows():
                tag = 'hrs_'+str(index.hour)
                pred.loc[index.strftime('%Y-%m-%d %H:%M:%S'), tag] = 1

            pred_x = pred[pred_col]
            pred_y = pred[['sbi']]

            try:
                sinfo = p.get_station_info()
                cno = get_cno_by_tot(int(sinfo[sinfo['sno'] == sno]['tot']))
                
                with open('pickle/model_cno_'+str(cno).zfill(2)+'.pickle', 'rb') as f:
                    model = pickle.load(f)
                m = Lasso(warm_start=True)
                m.coef_ = model.coef_
                m.fit(pred_x,pred_y)
                with open('pickle/model_cno_'+str(cno).zfill(2)+'.pickle', 'wb') as f:
                    pickle.dump(m, f, protocol=pickle.HIGHEST_PROTOCOL)

            except Exception as e:
                print('err:', sno, ', ',e)

        except Exception as e:
            print('err:', sno, ', ',e)




if __name__ == "__main__":
    #df = p.get_station_info()
    #print(df.tot)
    trainer_cno()
    #trainer_sno()
