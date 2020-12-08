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
mock qp module

RMR Messages:
 #define TS_QOE_PRED_REQ 30001
 #define TS_QOE_PREDICTION 30002
30001 is the message type QP receives from the driver;
sends out type 30002 which should be routed to TS.

"""

import json
import os
from mdclogpy import Logger
from ricxappframe.xapp_frame import RMRXapp, rmr

# pylint: disable=invalid-name
qp_xapp = None
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
    Function that processes messages for type 30001
    """
    logger.debug("predict handler received message type {}".format(summary[rmr.RMR_MS_MSG_TYPE]))
    logger.debug("adding somethign")
    logger.debug("message is " + summary[rmr.RMR_MS_PAYLOAD].decode())
    pred_req_msg = json.loads(summary[rmr.RMR_MS_PAYLOAD].decode())
    all_cells = {}
    ind = 0
    for ncell in pred_req_msg["CellMeasurements"]:
        if (ind == 0):
            all_cells[ncell["CellID"]] = [50000, 20000]
        else:
            all_cells[ncell["CellID"]] = [20000, 10000]
        ind += 1

    pred_msg = {}
    pred_msg[pred_req_msg["PredictionUE"]] = all_cells    
    self.predict_requests += 1
    # we don't use rts here; free this
    self.rmr_free(sbuf)
    # send a mock message based on input
    success = self.rmr_send(json.dumps(pred_msg).encode(), 30002)
    if success:
        logger.debug("predict handler: sent message successfully")
    else:
        logger.warning("predict handler: failed to send message")


def start(thread=False):
    """
    This is a convenience function that allows this xapp to run in Docker
    for "real" (no thread, real SDL), but also easily modified for unit testing
    (e.g., use_fake_sdl). The defaults for this function are for the Dockerized xapp.
    """
    logger.debug("QP xApp starting")
    global qp_xapp
    fake_sdl = os.environ.get("USE_FAKE_SDL", None)
    qp_xapp = RMRXapp(qp_default_handler, rmr_port=4560, post_init=post_init, use_fake_sdl=bool(fake_sdl))
    qp_xapp.register_callback(qp_predict_handler, 30001)
    qp_xapp.run(thread)


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
