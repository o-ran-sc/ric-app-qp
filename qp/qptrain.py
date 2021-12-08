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
import joblib


class DataNotMatchError(Exception):
    pass


class PROCESS(object):

    def __init__(self, data):
        self.diff = 0
        self.data = data

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
        """ Filter throughput parameters, call make_stationary() to check for Stationarity time series
        """
        df = self.data.copy()
        try:
            df = df[['pdcpBytesDl', 'pdcpBytesUl']]
        except DataNotMatchError:
            print('Parameters pdcpBytesDl, pdcpBytesUl does not exist in provided data')
            self.data = None
        self.data = df.loc[:, (df != 0).any(axis=0)]
        self.make_stationary()  # check for Stationarity and make the Time Series Stationary

    def valid(self):
        val = False
        if self.data is not None:
            df = self.data.copy()
            df = df.loc[:, (df != 0).any(axis=0)]
            if len(df) != 0 and df.shape[1] == 2:
                val = True
        return val


def train(db, cid):
    """
     Read the input file(based on cell id received from the main program)
     call process() to forecast the downlink and uplink of the input cell id
     Make a VAR model, call the fit method with the desired lag order.
    """
    db.read_data(meas='liveCell', cellid=cid)
    md = PROCESS(db.data)
    md.process()
    if md.valid():
        model = VAR(md.data)          # Make a VAR model
        model_fit = model.fit(10)            # call fit method with lag order
        file_name = 'qp/'+cid.replace('/', '')
        with open(file_name, 'wb') as f:
            joblib.dump(model_fit, f)     # Save the model with the cell id name
