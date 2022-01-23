# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 20:56:50 2019

@author: Maureen
"""

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import PredefinedSplit
from sklearn.model_selection import StratifiedKFold
from sklearn.feature_selection import RFECV

from sklearn.metrics import mean_squared_error

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
import logging

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
def rf(X, Y, kfold=3, model=None ,feature_set=None,rfecv_en=False):
    
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
    
    rf = RandomForestRegressor(random_state = 42)
    rf.fit(train_X, train_y)
    print('Base Parameter:')
    print(rf.get_params())

    if rfecv_en:
        # Create the RFE object and compute a cross-validated score
        min_features_to_select = 1  # Minimum number of features to consider
        rfecv = RFECV(estimator=rf, step=1, cv=StratifiedKFold(2),scoring='neg_mean_squared_error', min_features_to_select=min_features_to_select)
        selector = rfecv.fit(train_X, train_y)
                    
        print("RandomForest Optimal number of features : %d" % rfecv.n_features_)
        # Plot number of features VS. cross-validation scores
        plt.figure()
        plt.xlabel("Number of features selected")
        plt.ylabel("Cross validation score (nb of correct rmse)")
        plt.plot(range(min_features_to_select,len(rfecv.grid_scores_) + min_features_to_select),rfecv.grid_scores_)
        plt.show()
    
    
        train_X = train_X[:,selector.support_]
        test_X = test_X[:,selector.support_]

        
        rf = RandomForestRegressor(random_state = 42)
        rf.fit(train_X, train_y)
        print('RFECV Parameters in use:')
        print(rf.get_params())


    # Number of trees in random forest
    n_estimators = [int(x) for x in range(20,200,20)] #[int(x) for x in np.linspace(start = 200, stop = 2000, num = 10)]
    # Maximum number of levels in tree
    max_depth = [3, 5, 10, 20, 50]
    
    # Minimum number of samples required to split a node
    min_samples_split = [2, 5, 10]
    
    # Minimum number of samples required at each leaf node
    min_samples_leaf = [1, 2, 4]
    
    # Create the random grid
    grid_grid = {'n_estimators': n_estimators,
                   'max_depth': max_depth,
                   'min_samples_split': min_samples_split,
                   'min_samples_leaf': min_samples_leaf,
                  }
  
    rf_grid = GridSearchCV(estimator=rf, param_grid=grid_grid, scoring='neg_mean_squared_error', cv = ps2.split(), verbose=2, n_jobs=-1)
    # Fit the grid search model
    rf_grid.fit(train_X, train_y)
    BestPara_grid = rf_grid.best_params_
    print(rf_grid.best_params_)
    #cv_results_grid = rf_grid.cv_results_
    
    
    # Number of trees in random forest
    ets_unit =  BestPara_grid['n_estimators']
    n_estimators = [int(x) for x in range(ets_unit - 10, ets_unit + 10, 5)]
    max_depth = [BestPara_grid["max_depth"]]

    # Minimum number of samples required to split a node
    min_samples_split = []
    for x in range(BestPara_grid["min_samples_split"]-2,BestPara_grid["min_samples_split"]+2,1):
        if x>1:
            min_samples_split.append(int(x))
    # Minimum number of samples required at each leaf node
    min_samples_leaf = []
    for x in range(BestPara_grid["min_samples_leaf"]-1,BestPara_grid["min_samples_leaf"]+1,1):
        if x>0:
            min_samples_leaf.append(int(x))


    # Create the random grid
    grid_grid2 = { 'n_estimators': n_estimators,
                   'max_depth': max_depth,
                   'min_samples_split': min_samples_split,
                   'min_samples_leaf': min_samples_leaf
                   }
    
    rf_grid2 = GridSearchCV(estimator=rf, param_grid=grid_grid2, scoring='neg_mean_squared_error', cv = ps2.split(), verbose=2, n_jobs=-1)
    # Fit the grid search model
    rf_grid2.fit(train_X, train_y)
    #BestPara_grid2 = rf_grid2.best_params_
    print(rf_grid2.best_params_)


    #prediction
    predict_y=rf_grid2.predict(test_X)
    predict_y_grid=rf_grid.predict(test_X)
    predict_y_base=rf.predict(test_X)

    #rmse 
    errors_Grid_CV = np.sqrt(mean_squared_error(predict_y_grid,test_y))
    errors_Grid2_CV = np.sqrt(mean_squared_error(predict_y,test_y))
    errors_baseline = np.sqrt(mean_squared_error(predict_y_base,test_y))

    results = [errors_baseline,errors_Grid_CV, errors_Grid2_CV]
    
    print("Random Forest Result: ",results)
    if rfecv_en:
        return rf_grid2.best_estimator_, results, rf_grid2.best_params_, selector.support_
    else:
        return rf_grid2.best_estimator_, results, rf_grid2.best_params_, None
