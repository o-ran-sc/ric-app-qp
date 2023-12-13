# ==================================================================================
#  Copyright (c) 2020 HCL Technologies Limited.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ==================================================================================

from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller
from mdclogpy import Logger
from exceptions import DataNotMatchError
from sklearn.metrics import mean_squared_error
from math import sqrt
import pandas as pd
import joblib
import warnings
warnings.filterwarnings("ignore")

logger = Logger(name=__name__)


class PROCESS(object):

    def __init__(self, data):
        self.diff = 0
        self.data = data

    def input_data(self):
        try:
            self.data = self.data[db.thptparam]
            self.data = self.data.fillna(method='bfill')
        except DataNotMatchError:
            logger.error('Parameters Downlink throughput and Uplink throughput does not exist in provided data')
            self.data = None

    def adfuller_test(self, series, thresh=0.05, verbose=False):
        """ADFuller test for Stationarity of given series and return True or False"""
        r = adfuller(series, autolag='AIC')
        output = {'test_statistic': round(r[0], 4), 'pvalue': round(r[1], 4), 'n_lags': round(r[2], 4), 'n_obs': r[3]}
        p_value = output['pvalue']
        if p_value <= thresh:
            return True
        else:
            return False

    def make_stationary(self):
        """ call adfuller_test() to check for stationary
            If the column is stationary, perform 1st differencing and return data"""
        df = self.data.copy()
        res_adf = []
        for name, column in df.iteritems():
            res_adf.append(self.adfuller_test(column))  # Perform ADF test
        if not all(res_adf):
            self.data = df.diff().dropna()
            self.diff += 1

    def invert_transformation(self, inp, forecast):
        """Revert back the differencing to get the forecast to original scale."""
        if self.diff == 0:
            return forecast
        df = forecast.copy()
        columns = inp.columns
        for col in columns:
            df[col] = inp[col].iloc[-1] + df[col].cumsum()
        self.diff = 0
        return df

    def process(self):
        self.input_data()
        self.make_stationary()  # check for Stationarity and make the Time Series Stationary

    def constant(self):
        val = True
        df = self.data.copy()
        df = df[db.thptparam]
        df = df.drop_duplicates()
        df = df.loc[:, df.apply(pd.Series.nunique) != 1]
        if df is not None:
            df = df.dropna()
            df = df.loc[:, (df != 0).any(axis=0)]
            if len(df) >= 10:
                val = False
        return val

    def evaluate_var(self, X, lag):
        # prepare training dataset
        train_size = int(len(X) * 0.75)
        train, test = X[0:train_size], X[train_size:]
        # make predictions
        model = VAR(train)
        model_fit = model.fit(lag)
        predictions = model_fit.forecast(y=train.values, steps=len(test))
        # calculate out of sample error
        rmse = sqrt(mean_squared_error(test, predictions))
        return rmse

    def optimize_lag(self, df):
        lag = range(1, 20, 1)
        df = df.astype('float32')
        best_score, best_lag = float("inf"), None
        for l in lag:
            try:
                rmse = self.evaluate_var(df, l)
                if rmse < best_score:
                    best_score, best_lag = rmse, l
            except ValueError as v:
                print(v)
        # print('Best VAR%s RMSE=%.3f' % (best_lag, best_score))
        return best_lag


def train_cid(cid):
    """
     Read the input file(based on cell id received from the main program)
     call process() to forecast the downlink and uplink of the input cell id
     Make a VAR model, call the fit method with the desired lag order.
    """
    # print(f'Training for {cid}')
    db.read_data(cellid=cid, limit=4800)
    md = PROCESS(db.data)
    if md.data is not None and not md.constant():
        md.process()
        lag = md.optimize_lag(md.data)
        model = VAR(md.data)          # Make a VAR model
        try:
            model_fit = model.fit(lag)            # call fit method with lag order
            file_name = 'src/'+cid.replace('/', '')
            with open(file_name, 'wb') as f:
                joblib.dump(model_fit, f)     # Save the model with the cell id name
        except ValueError as v:
            print("****************************************", v)


def train(database, cid):
    global db
    db = database
    train_cid(cid)
