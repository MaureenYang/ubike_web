from sklearn.model_selection import PredefinedSplit
from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import Ridge
from sklearn.model_selection import StratifiedKFold
from sklearn.feature_selection import RFECV
from sklearn.metrics import mean_squared_error
import math
import numpy as np
import matplotlib.pyplot as plt
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


def ridge(X, Y, kfold=3, feature_set=None,rfecv_en=False):

    arr = index_splitter(N = len(X), fold = kfold)
    ps = PredefinedSplit(arr)

    for train, test in ps.split():
        train_index = train
        test_index = test

    train_X, train_y = X.values[train_index,:], Y.values[train_index]
    test_X, test_y = X.values[test_index,:], Y.values[test_index]

    arr = index_splitter(N = len(train_X), fold = kfold)
    ps2 = PredefinedSplit(arr)

    tscv = TimeSeriesSplit(n_splits=10)

    # base
    ridge = Ridge(random_state = 42)
    ridge.fit(train_X, train_y)
    print('Base Parameters in use:')
    print(ridge.get_params())

    if rfecv_en:
    
        # Create the RFE object and compute a cross-validated score
        min_features_to_select = 1  # Minimum number of features to consider
        rfecv = RFECV(estimator=ridge, step=1, cv=StratifiedKFold(2),scoring='neg_mean_squared_error', min_features_to_select=min_features_to_select)
        selector = rfecv.fit(train_X, train_y)
                    
        print("Ridge Optimal number of features : %d" % rfecv.n_features_)
        # Plot number of features VS. cross-validation scores
        plt.figure()
        plt.xlabel("Number of features selected")
        plt.ylabel("Cross validation score (nb of correct rmse)")
        plt.plot(range(min_features_to_select,len(rfecv.grid_scores_) + min_features_to_select),rfecv.grid_scores_)
        plt.show()
    
    
        train_X = train_X[:,selector.support_]
        test_X = test_X[:,selector.support_]
        
        ridge = Ridge(random_state = 42)
        ridge.fit(train_X, train_y)
        print('RFECV Parameters in use:')
        print(ridge.get_params())


    # grid search
    alpha_log = np.linspace(-8,5,14)

    alpha = []
    for i in alpha_log:
        a = math.pow(10,i)
        alpha = alpha + [a]

    grid_grid = {'alpha': alpha}
    ridge_grid = GridSearchCV(estimator=ridge, param_grid=grid_grid, scoring='neg_mean_squared_error', cv = ps2.split(), verbose=2, n_jobs=-1)

    # Fit the grid search model
    ridge_grid.fit(train_X, train_y)
    BestPara_grid = ridge_grid.best_params_
    print("grid search, best parameter:", ridge_grid.best_params_)
    #cv_results_grid = ridge_grid.cv_results_
    
    lr_unit =  BestPara_grid['alpha']/10
    alpha = [x for x in np.linspace(start = lr_unit, stop = lr_unit*99, num = 99)]

    grid_grid = {'alpha': alpha}
    ridge_grid2 = GridSearchCV(estimator=ridge, param_grid=grid_grid, scoring='neg_mean_squared_error', cv = tscv, verbose=2, n_jobs=-1)

    # Fit the grid search model
    ridge_grid2.fit(train_X, train_y)
    BestPara_grid = ridge_grid2.best_params_
    print("grid search, best parameter:", ridge_grid2.best_params_)
    #cv_results_grid2 = ridge_grid2.cv_results_    
    

    #prediction
    predict_y_grid = ridge_grid.predict(test_X)
    predict_y_base = ridge.predict(test_X)
    predict_y_grid2 = ridge_grid2.predict(test_X)

    # Performance metrics
    errors_Grid_CV = np.sqrt(mean_squared_error(predict_y_grid,test_y))
    errors_Grid2_CV = np.sqrt(mean_squared_error(predict_y_grid2,test_y))
    errors_baseline = np.sqrt(mean_squared_error(predict_y_base,test_y))

    results = [errors_Grid2_CV,errors_Grid_CV,errors_baseline]
    
    print('ridge results:',results)

    if False:
        #feature importance
        num_feature = len(ridge_grid2.best_estimator_.coef_[0])
        #print('num_feature:',num_feature)
        label_name = X.keys()
        #print(ridge_grid2.best_estimator_.coef_[0])
        #print(range(1,num_feature*4,4))
        #print(label_name)  
        plt.figure(figsize=(24,6))
        plt.bar(range(1,num_feature*4,4), ridge_grid2.best_estimator_.coef_[0])
        plt.xticks(range(1,num_feature*4,4), label_name)
        plt.title("Ridge Feature Importances"+",kfold="+str(kfold))
        plt.show()
        
    if rfecv_en:
        return ridge_grid2.best_estimator_, results, ridge_grid2.best_params_, selector.support_
    else:
        return ridge_grid2.best_estimator_, results, ridge_grid2.best_params_, None
