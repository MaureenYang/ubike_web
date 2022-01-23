# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 20:56:50 2019

@author: Maureen

"""

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import PredefinedSplit
from sklearn.model_selection import GridSearchCV

from sklearn.metrics import mean_squared_log_error
from sklearn.metrics import mean_squared_error

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math

import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")

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
def gb(X, Y, kfold=3, feature_set=None,rfecv_en=False):
    
    arr = index_splitter(N = len(X), fold = kfold)
    ps = PredefinedSplit(arr)

    for train, test in ps.split():
        train_index = train
        test_index = test

    train_X, train_y = X.values[train_index,:], Y.values[train_index]
    test_X, test_y = X.values[test_index,:], Y.values[test_index]

    arr = index_splitter(N = len(train_X), fold = kfold)
    ps2 = PredefinedSplit(arr)
    
    
    gb = GradientBoostingRegressor(random_state = 42)
    print('Base parameter:')
    print(gb.get_params())
    gb.fit(train_X, train_y)
    

    #grid search
    lr_log = np.linspace(-8,5,14)

    lr = []
    for i in lr_log:
        a = math.pow(10,i)
        lr = lr + [a]
        
    n_estimators = [int(x) for x in range(20,200,20)] #[int(x) for x in np.linspace(start = 10, stop = 200, num = 50)]
    # Maximum number of levels in tree
    max_depth = [3, 5, 10, 20, 50]
    # Minimum number of samples required to split a node
    min_samples_split = [2, 5, 10]
    # Minimum number of samples required at each leaf node
    min_samples_leaf = [1, 2, 4]


    # Create the random grid
    grid_grid = {'learning_rate' : lr,
                   'n_estimators': n_estimators,
                   'max_depth': max_depth,
                   'min_samples_split': min_samples_split,
                   'min_samples_leaf': min_samples_leaf,
                   }
    
    
    gb_grid = GridSearchCV(estimator=gb, param_grid=grid_grid, scoring='neg_mean_squared_error', cv = ps2.split(), verbose=2, n_jobs=-1)
    gb_grid.fit(train_X, train_y)
    BestPara_grid = gb_grid.best_params_
    print('Grid parameter:')
    print(gb_grid.best_params_)


    # Number of trees in random forest
    lr_unit =  BestPara_grid['learning_rate']
    lr = [x for x in np.linspace(start = lr_unit, stop = lr_unit*9, num = 9)]
    
    ets_unit =  BestPara_grid['n_estimators']
    n_estimators = [int(x) for x in range(ets_unit - 20, ets_unit + 20, 5)]
    
    max_depth = [BestPara_grid["max_depth"]]
    

    # Minimum number of samples required to split a node
    min_samples_split = []
    for x in range(BestPara_grid["min_samples_split"]-2,BestPara_grid["min_samples_split"]+2,1):
        if x>1:
            min_samples_split.append(int(x))
            
    # Minimum number of samples required at each leaf node
    min_samples_leaf = [BestPara_grid["min_samples_leaf"]]
    '''
    for x in range(BestPara_grid["min_samples_leaf"]-1,BestPara_grid["min_samples_leaf"]+1,1):
        if x>0:
            min_samples_leaf.append(int(x))
    '''

    # Create the random grid
    grid_grid2 = {'learning_rate' : lr,
                  'n_estimators': n_estimators,
                   'max_depth': max_depth,
                   'min_samples_split': min_samples_split,
                   'min_samples_leaf': min_samples_leaf,
                   }
    
    gb_grid2 = GridSearchCV(estimator=gb, param_grid=grid_grid2, scoring='neg_mean_squared_error', cv = ps2.split(), verbose=2, n_jobs=-1)
    
    # Fit the grid search model
    gb_grid2.fit(train_X, train_y)
    BestPara_grid = gb_grid2.best_params_
    print(gb_grid2.best_params_)


    #prediction
    predict_y=gb_grid2.predict(test_X)
    predict_y_grid=gb_grid.predict(test_X)
    predict_y_base=gb.predict(test_X)
  
    
    #RMSE
    errors_baseline = np.sqrt(mean_squared_error(predict_y_base,test_y))
    errors_Grid_CV = np.sqrt(mean_squared_error(predict_y_grid,test_y))
    errors_Grid2_CV = np.sqrt(mean_squared_error(predict_y,test_y))

    results = [errors_baseline, errors_Grid_CV, errors_Grid2_CV]

    print('gradient boost results:',results)

    return gb_grid2.best_estimator_, results, gb_grid2.best_params_, None
