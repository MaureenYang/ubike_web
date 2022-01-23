from sklearn.model_selection import PredefinedSplit
from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import StratifiedKFold
from sklearn.feature_selection import RFECV

from sklearn.linear_model import Lasso

from sklearn.metrics import mean_squared_error
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd



def index_splitter(N, fold):
    index_split = []
    test_num = int(N/fold)
    train_num = N-test_num

    for i in range(0,train_num):
        index_split.append(-1)

    for i in range(train_num,N):
        index_split.append(0)

    return index_split


def lasso(X, Y, kfold=3, feature_set=None,rfecv_en=False):

    arr = index_splitter(N = len(X), fold = kfold)
    ps = PredefinedSplit(arr)

    for train, test in ps.split():
        train_index = train
        test_index = test

    train_X, train_y = X.values[train_index,:], Y.values[train_index]
    test_X, test_y = X.values[test_index,:], Y.values[test_index]
        
    arr = index_splitter(N = len(train_X), fold = kfold)
    ps2 = PredefinedSplit(arr)

    # base
    lasso = Lasso(random_state = 42, tol=100)
    lasso.fit(train_X, train_y)
    print('Base Parameters in use:')
    print(lasso.get_params())

    if rfecv_en:
        # Create the RFE object and compute a cross-validated score
        min_features_to_select = 1  # Minimum number of features to consider
        rfecv = RFECV(estimator=lasso, step=1, cv=ps2.split(),scoring='neg_mean_squared_error', min_features_to_select=min_features_to_select)
        selector = rfecv.fit(train_X, train_y)
                    
        print("Lasso Optimal number of features : %d" % rfecv.n_features_)
        # Plot number of features VS. cross-validation scores
        plt.figure()
        plt.xlabel("Number of features selected")
        plt.ylabel("Cross validation score (nb of correct rmse)")
        plt.plot(range(min_features_to_select,len(rfecv.grid_scores_) + min_features_to_select),rfecv.grid_scores_)
        plt.show()
    
    
        train_X = train_X[:,selector.support_]
        test_X = test_X[:,selector.support_]
        
        lasso = Lasso(random_state = 42)
        lasso.fit(train_X, train_y)
        print('RFECV Parameters in use:')
        print(lasso.get_params())


    # grid search
    alpha_log = np.linspace(-8,5,14)

    alpha = []
    for i in alpha_log:
        a = math.pow(10,i)
        alpha = alpha + [a]

    grid_grid = {'alpha': alpha}
    
    print(grid_grid)
    lasso_grid = GridSearchCV(estimator=lasso, param_grid=grid_grid, scoring='neg_mean_squared_error', cv = ps2.split(), verbose=2, n_jobs=-1)

    # Fit the grid search model
    lasso_grid.fit(train_X, train_y)
    BestPara_grid = lasso_grid.best_params_
    print("grid search, best parameter:", lasso_grid.best_params_)
    #cv_results_grid = lasso_grid.cv_results_


    lr_unit =  BestPara_grid['alpha']/10
    alpha = [x for x in np.linspace(start = lr_unit, stop = lr_unit*99, num = 99)]

    grid_grid = {'alpha': alpha}
    lasso_grid2 = GridSearchCV(estimator=lasso, param_grid=grid_grid, scoring='neg_mean_squared_error', cv = ps2.split(), verbose=2, n_jobs=-1)

    # Fit the grid search model
    lasso_grid2.fit(train_X, train_y)
    print("grid search, best parameter:", lasso_grid2.best_params_)
    #cv_results_grid2 = lasso_grid2.cv_results_    


    #prediction
    predict_y_grid2 = lasso_grid2.predict(test_X)
    predict_y_grid = lasso_grid.predict(test_X)
    predict_y_base = lasso.predict(test_X)

    # Performance metrics
    errors_Grid2_CV = np.sqrt(mean_squared_error(predict_y_grid2,test_y))
    errors_Grid_CV = np.sqrt(mean_squared_error(predict_y_grid,test_y))
    errors_baseline = np.sqrt(mean_squared_error(predict_y_base,test_y))

    results = [errors_Grid2_CV, errors_Grid_CV,errors_baseline]
    print('lasso results:',results)
   
    
    if False:
        #feature importance
        label_name = X.keys()
        #print(lasso_grid2.best_estimator_.coef_)
        #print(label_name)   
        coef_lab = pd.DataFrame(lasso_grid2.best_estimator_.coef_,index=label_name)
        coef_lab = coef_lab.sort_values(by=0)
        label_name = coef_lab.index
        num_feature = len(lasso_grid2.best_estimator_.coef_)
        plt.figure(figsize=(60,7))
        plt.bar(range(1,num_feature*4,4), coef_lab[0])
        plt.xticks(range(1,num_feature*4,4), label_name)
        plt.title("Lasso Feature Importances"+",kfold="+str(kfold))
        plt.show()
    
     
    if rfecv_en:
        return lasso_grid2.best_estimator_, results, lasso_grid2.best_params_, selector.support_
    else:
        return lasso_grid2.best_estimator_, results, lasso_grid2.best_params_, None
