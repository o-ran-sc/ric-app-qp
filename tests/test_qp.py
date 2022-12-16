# ==================================================================================
#       Copyright (c) 2020 HCL Technologies Limited.
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
import json
import time
from contextlib import suppress
from src import main
from ricxappframe.xapp_frame import Xapp, RMRXapp

mock_qp_xapp = None
mock_ts_xapp = None

"""
 these tests are not currently parallelizable (do not use this tox flag)
 I would use setup_module, however that can't take monkeypatch fixtures
 Currently looking for the best way to make this better:
 https://stackoverflow.com/questions/60886013/python-monkeypatch-in-pytest-setup-module
"""


def test_init_xapp(monkeypatch):

    # monkeypatch post_init to set the data we want
    def fake_post_init(self):
        self.predict_requests = 0

    # patch
    monkeypatch.setattr("src.main.post_init", fake_post_init)

    # start qp
    main.start(thread=True)


def test_database_connection(monkeypatch):
    main.connectdb(thread=True)


def test_training(monkeypatch, qp_train):
    main.train_model(qp_train)


def test_predict(monkeypatch, ts_to_qp):
    main.predict(ts_to_qp)


def test_rmr_flow(monkeypatch, ts_to_qp, qp_prediction):
    """
    this flow mocks out the xapps on both sides of QP.
    It first stands up a mock ts, then it starts up a mock qp-driver
    which will immediately send requests to the running qp.
    """

    expected_result = {}

    # define a mock traffic steering xapp that listens on 4563
    def mock_ts_default_handler(self, summary, sbuf):
        pass

    def mock_ts_prediction_handler(self, summary, sbuf):
        nonlocal expected_result  # closures ftw
        pay = json.loads(summary["payload"])
        expected_result = pay

    global mock_ts_xapp
    mock_ts_xapp = RMRXapp(mock_ts_default_handler, rmr_port=4563, use_fake_sdl=True)
    mock_ts_xapp.register_callback(mock_ts_prediction_handler, 30002)
    mock_ts_xapp.run(thread=True)

    time.sleep(1)

    # define a mock qp xapp that listens on 4560
    def mock_qp_entry(self):

        # good traffic steering request
        val = json.dumps(ts_to_qp).encode()
        self.rmr_send(val, 30000)

        # should trigger the default handler and do nothing
        val = json.dumps({"test send 60001": 2}).encode()
        self.rmr_send(val, 60001)

    global mock_qp_xapp
    mock_qp_xapp = Xapp(entrypoint=mock_qp_entry, rmr_port=4560, use_fake_sdl=True)
    mock_qp_xapp.run()  # this will return since entry isn't a loop


def teardown_module():
    """
    this is like a "finally"; the name of this function is pytest magic
    safer to put down here since certain failures above can lead to pytest never returning
    for example if an exception gets raised before stop is called in any test function above,
    pytest will hang forever
    """
    with suppress(Exception):
        mock_ts_xapp.stop()
    with suppress(Exception):
        mock_qp_xapp.stop()
    with suppress(Exception):
        main.stop()
