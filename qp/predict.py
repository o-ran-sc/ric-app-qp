# ==================================================================================
#       Copyright (c) 2020 AT&T Intellectual Property.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ==================================================================================
"""
Machine learning prediction component of QP xAPP
"""

import numpy as np
import pandas as pd
import datetime
from json import loads, dumps
from sklearn.linear_model import LinearRegression

# How far in the future to make a prediction
predinterval = datetime.timedelta(seconds=30)

# How far back in the past to consider data used in making predictions
predwindow = datetime.timedelta(seconds=900)

# uehist is the dict used to store the historical measurement data to make predictions
# It has an entry for each UE encountered
# Each entry is itself a dict with a key for each CellID encountered as a neighbor of that UE
# Each of these dicts is a pandas dataframe with a row for each time and metric:
# Dataframe fields: ts (timestamp), dl (dowload bytes), ul (upload bytes)
uehist = {}


def qpprediction(reqstr: str):
    '''Takes a JSON string with a message from qp driver and returns a JSON string with a prediction for the
    UE in the message.'''

    req = loads(reqstr)
    ueid = req['PredictionUE']
    uedict = req['UEMeasurements']

    # Use this field as the current time for the purpose of predicting
    now = pd.to_datetime(uedict['MeasTimestampUEPDCPBytes'])

    # Create an x value to use for predictions predinterval in the future from now
    predx = np.array([np.datetime64(now + predinterval)]).astype(float).reshape(-1, 1) * 1000

    # Fetch this UE's history into hist, or create a new dict if it's never been seen before
    hist = uehist[ueid] if ueid in uehist else {}

    # Dictionary with a key for each CellID we have seen
    preddict = {}

    for c in req['CellMeasurements']:
        cellid = c['CellID']
        # Fetch this CellID's df, or create an empty df if we've never seen this CellID before
        chist = hist[cellid] if cellid in hist else pd.DataFrame(columns=['ts', 'dl', 'ul'])
        # Trim out every entry earlier than predwindow before now
        chist = chist[chist['ts'] >= now - predwindow]
        # Create and add entry to df
        row = {'ts': pd.to_datetime(c['MeasTimestampPDCPBytes']), 'dl': c['PDCPBytesDL'], 'ul': c['PDCPBytesUL']}
        chist = chist.append(row, ignore_index=True)
        # Update the historical data df for this CellID
        hist[cellid] = chist
        # Create and fit a linear model to predict both dl and ul
        x = chist[['ts']]
        y = chist[['dl', 'ul']]
        model = LinearRegression().fit(x, y)
        # Add this prediction to dict used for retuned value
        preddict[cellid] = [int(val) for val in model.predict(predx)[0]]

    # Update the historical data for this UE
    uehist[ueid] = hist

    return dumps({ueid: preddict})
