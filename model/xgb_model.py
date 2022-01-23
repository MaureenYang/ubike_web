# -*- coding: utf-8 -*-
"""
Created on Sun May 23 01:12:12 2021

@author: Maureen
"""

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import PredefinedSplit
from sklearn.model_selection import GridSearchCV

from sklearn.model_selection import StratifiedKFold
from sklearn.feature_selection import RFECV

from sklearn.metrics import mean_squared_log_error
from sklearn.metrics import mean_squared_error

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math


def index_splitter(N, fold):
    index_split = []
    test_num = int(N/fold)
    train_num = N-test_num

    for i in range(0,train_num):
        index_split.append(-1)

    for i in range(train_num,N):
        index_split.append(0)

    return index_split


# Number of trees in random forest
def xgb(X, Y, kfold=3, feature_set=None,rfecv_en=False):
    
    arr = index_splitter(N = len(X), fold = kfold)
    ps = PredefinedSplit(arr)

    for train, test in ps.split():
        train_index = train
        test_index = test


    train_X, train_y = X.values[train_index,:], Y.values[train_index]
    test_X, test_y = X.values[test_index,:], Y.values[test_index]

    arr = index_splitter(N = len(train_X), fold = kfold)
    ps2 = PredefinedSplit(arr)


    #baseline
    xgb = XGBRegressor(random_state = 42)
    xgb.fit(train_X, train_y)
    print('Base Parameters:\n')
    #print(xgb.get_params())

    if rfecv_en:
        # Create the RFE object and compute a cross-validated score
        min_features_to_select = 1  # Minimum number of features to consider
        rfecv = RFECV(estimator=xgb, step=1, cv=StratifiedKFold(2),scoring='neg_mean_squared_error', min_features_to_select=min_features_to_select)
        selector = rfecv.fit(train_X, train_y)
                    
        print("XGBoost Optimal number of features : %d" % rfecv.n_features_)
        # Plot number of features VS. cross-validation scores
        plt.figure()
        plt.xlabel("Number of features selected")
        plt.ylabel("Cross validation score (nb of correct rmse)")
        plt.plot(range(min_features_to_select,len(rfecv.grid_scores_) + min_features_to_select),rfecv.grid_scores_)
        plt.show()
    
    
        train_X = train_X[:,selector.support_]
        test_X = test_X[:,selector.support_]
        
        xgb = XGBRegressor(random_state = 42)
        xgb.fit(train_X, train_y)
        print('RFECV Parameters in use:')
        print(xgb.get_params())


    #grid search
    lr_log = np.linspace(-20,-15,6)

    lr = []
    for i in lr_log:
        a = math.pow(10,i)
        lr = lr + [a]
        
    n_estimators = [int(x) for x in range(20,200,20)] #[int(x) for x in np.linspace(start = 10, stop = 200, num = 50)]

    # Maximum number of levels in tree
    max_depth = [3, 5, 10, 20, 50]
    
    # Minimum number of samples required to split a node
    # min_samples_split = [5, 10]
    
    # Minimum number of samples required at each leaf node
    min_child_weight = [2, 4]
    
    
    # Create the grid 
    grid_grid = {'eta' : lr,
                 'n_estimators': n_estimators,
                 'max_depth': max_depth,
                 'min_child_weight':min_child_weight,
                 'booster':['gblinear']
                  }

    xgb_grid = GridSearchCV(estimator=xgb, param_grid=grid_grid, scoring='neg_mean_squared_error',
                                  cv = ps2.split(), verbose=2, n_jobs=-1)
    
    xgb_grid.fit(train_X, train_y)
    BestPara_grid = xgb_grid.best_params_
    print('Grid Parameters:')
    print(xgb_grid.best_params_)
    

    # second run, grid search
    eta_unit =  BestPara_grid['eta']
    eta = [x for x in np.linspace(start = eta_unit, stop = eta_unit*9, num = 9)]
    
    ets_unit =  BestPara_grid['n_estimators']
    n_estimators = [int(x) for x in range(ets_unit - 20, ets_unit + 20, 5)]
    
    max_depth = [BestPara_grid["max_depth"]]
    min_child_weight = [BestPara_grid["min_child_weight"]]
    
    grid_grid2 = {  'eta' : eta,
                    'n_estimators': n_estimators,
                    'max_depth': max_depth,
                    'min_child_weight':min_child_weight,
                    'booster':['gblinear']
                 }
    
    xgb_grid2 = GridSearchCV(estimator=xgb, param_grid=grid_grid2, scoring='neg_mean_squared_error', cv = ps2.split(), verbose=2, n_jobs=-1)    
    xgb_grid2.fit(train_X, train_y)
    print('Grid v2 Parameters:')
    print(xgb_grid2.best_params_)
    
    
    #predict
    predict_y_base=xgb.predict(test_X)
    predict_y_grid=xgb_grid.predict(test_X)
    predict_y_grid2 = xgb_grid2.predict(test_X)
    
    #RMSE
    errors_baseline = np.sqrt(mean_squared_error(predict_y_base,test_y))
    errors_Grid_CV = np.sqrt(mean_squared_error(predict_y_grid,test_y))
    errors_Grid2_CV = np.sqrt(mean_squared_error(predict_y_grid2,test_y))

    results = [errors_baseline,errors_Grid_CV,errors_Grid2_CV]
    print('xgboost results:',results)
    
    if rfecv_en:
        return xgb_grid2.best_estimator_, results, xgb_grid2.best_params_,selector.support_
    else:
        return xgb_grid2.best_estimator_, results, xgb_grid2.best_params_, None

