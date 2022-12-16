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
# import pandas as pd
import os
import joblib
import pandas as pd
from qptrain import PROCESS


def forecast(data, cid, nobs=1):
    """
     forecast the time series using the saved model.
    """
    ps = PROCESS(data.copy())
    if ps.data is None:
        return
    data = ps.data
    pred = data.tail(1).values
    if os.path.isfile('src/'+cid) and not ps.constant():
        model = joblib.load('src/'+cid)
        pred = model.forecast(y=data.values, steps=nobs)

    df_f = pd.DataFrame(pred, columns=data.columns)
    df_f.index = pd.date_range(start=data.index[-1], freq='10ms', periods=len(df_f))
    df_f = df_f[data.columns].fillna(0).astype(int)
    df_f = ps.invert_transformation(data, df_f)
    return df_f
