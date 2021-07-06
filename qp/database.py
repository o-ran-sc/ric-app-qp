# ==================================================================================
#       Copyright (c) 2020 AT&T Intellectual Property.
#       Copyright (c) 2020 HCL Technologies Limited.
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
from influxdb import DataFrameClient
import pandas as pd
import datetime


class NoDataError(Exception):
    pass


class DATABASE(object):

    def __init__(self, dbname, user='root', password='root', host='r4-influxdb.ricplt', port='8086'):
        self.client = DataFrameClient(host, port, user, password, dbname)
        self.data = None

    def read_data(self, meas='ueMeasReport', limit=100000, cellid=False, ueid=False):
        query = """select * from """ + meas

        if cellid:
            query += " where nrCellIdentity= '" + cellid + "'"

        if ueid:
            query += """ where "ue-id"  = \'{}\'""".format(ueid)
        query += "  ORDER BY DESC LIMIT " + str(limit)
        result = self.client.query(query)
        try:
            if len(result) != 0:
                # print("Querying data : " + meas + " : size - " + str(len(result[meas])))
                self.data = result[meas]
                self.data['measTimeStampRf'] = self.data.index
            else:
                raise NoDataError

        except NoDataError:
            if cellid:
                print('Data not found for ' + meas + ' CellID : '+cellid)
            elif ueid:
                print('Data not found for ' + meas + ' UEID : '+ueid)
            else:
                print('Data not found for ' + meas)
            pass

    def write_prediction(self, df, meas_name='QP'):
        df.index = pd.date_range(start=datetime.datetime.now(), freq='10ms', periods=len(df))
        self.client.write_points(df, meas_name)


class DUMMY:

    def __init__(self):
        self.ue = pd.DataFrame([[1002, "c2/B13", 8, 69, 65, 113, 0.1, 0.1, "Waiting passenger 9", -882, -959, pd.to_datetime("2021-05-12T07:43:51.652")]], columns=["du-id", "nbCellIdentity", "prb_usage", "rsrp", "rsrq", "rssinr", "throughput", "targetTput", "ue-id", "x", "y", "measTimeStampRf"])
        self.cell = pd.read_csv('qp/dummy.csv')
        self.data = None

    def read_data(self, meas='ueMeasReport', limit=100000, cellid=False, ueid=False):
        if ueid:
            self.data = self.ue.head(limit)
        if cellid:
            self.data = self.cell.head(limit)

    def write_prediction(self, df, meas_name='QP'):
        pass
