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
"""
qp module main -- using Time series ML predictor

RMR Messages:
 #define TS_UE_LIST 30000
 #define TS_QOE_PREDICTION 30002
30000 is the message type QP receives from the TS;
sends out type 30002 which should be routed to TS.

"""
import os
import json
from mdclogpy import Logger
from ricxappframe.xapp_frame import RMRXapp, rmr
from prediction import forecast
from qptrain import train
from database import DATABASE, DUMMY
from exceptions import DataNotMatchError
import warnings
# import schedule
warnings.filterwarnings("ignore")

# pylint: disable=invalid-name
qp_xapp = None
db = None
logger = Logger(name=__name__)


def post_init(self):
    """
    Function that runs when xapp initialization is complete
    """
    self.predict_requests = 0
    logger.debug("QP xApp started")


def qp_default_handler(self, summary, sbuf):
    """
    Function that processes messages for which no handler is defined
    """
    logger.debug("default handler received message type {}".format(summary[rmr.RMR_MS_MSG_TYPE]))
    # we don't use rts here; free this
    self.rmr_free(sbuf)


def qp_predict_handler(self, summary, sbuf):
    """
    Function that processes messages for type 30000
    """
    logger.debug("predict handler received payload {}".format(summary[rmr.RMR_MS_PAYLOAD]))
    pred_msg = predict(summary[rmr.RMR_MS_PAYLOAD])
    self.predict_requests += 1
    # we don't use rts here; free this
    self.rmr_free(sbuf)
    success = self.rmr_send(pred_msg.encode(), 30002)
    logger.debug("Sending message to ts : {}".format(pred_msg))  # For debug purpose
    if success:
        logger.debug("predict handler: sent message successfully")
    else:
        logger.warning("predict handler: failed to send message")


def cells(ue):
    """
        Extract neighbor cell id for a given UE
    """
    db.read_data(ueid=ue)
    df = db.data
    cells = []
    if df is not None:
        nbc = df.filter(regex=db.nbcells).values[0].tolist()
        srvc = df.filter(regex=db.servcell).values[0].tolist()
        cells = srvc+nbc
    return cells


def predict(payload):
    """
     Function that forecast the time series
    """
    output = {}
    payload = json.loads(payload)
    ue_list = payload['UEPredictionSet']
    for ueid in ue_list:
        tp = {}
        cell_list = cells(ueid)
        for cid in cell_list:
            train_model(cid)
            mcid = cid.replace('/', '')
            db.read_data(cellid=cid, limit=101)
            if db.data is not None and len(db.data) != 0:
                try:
                    inp = db.data[db.thptparam]
                except DataNotMatchError:
                    logger.debug("UL/DL parameters do not exist in provided data")
                df_f = forecast(inp, mcid, 1)
                if df_f is not None:
                    tp[cid] = df_f.values.tolist()[0]
                    df_f[db.cid] = cid
                    db.write_prediction(df_f)
                else:
                    tp[cid] = [None, None]
        output[ueid] = tp
    return json.dumps(output)


def train_model(cid):
    if not os.path.isfile('src/'+cid):
        train(db, cid)


def start(thread=False):
    """
    This is a convenience function that allows this xapp to run in Docker
    for "real" (no thread, real SDL), but also easily modified for unit testing
    (e.g., use_fake_sdl). The defaults for this function are for the Dockerized xapp.
    """
    logger.debug("QP xApp starting")
    global qp_xapp
    connectdb(thread)
    fake_sdl = os.environ.get("USE_FAKE_SDL", None)
    qp_xapp = RMRXapp(qp_default_handler, rmr_port=4560, post_init=post_init, use_fake_sdl=bool(fake_sdl))
    qp_xapp.register_callback(qp_predict_handler, 30000)
    qp_xapp.run(thread)


def connectdb(thread=False):
    # Create a connection to InfluxDB if thread=True, otherwise it will create a dummy data instance
    global db
    if thread:
        db = DUMMY()
    else:
        db = DATABASE()
    success = False
    while not success and not thread:
        success = db.connect()


def stop():
    """
    can only be called if thread=True when started
    TODO: could we register a signal handler for Docker SIGTERM that calls this?
    """
    global qp_xapp
    qp_xapp.stop()


def get_stats():
    """
    hacky for now, will evolve
    """
    global qp_xapp
    return {"PredictRequests": qp_xapp.predict_requests}
