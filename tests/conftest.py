# ==================================================================================
#       Copyright (c) 2020 AT&T Intellectual Property.
#       Copyright (c) 2021 HCL Technologies Limited.
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


import pytest


@pytest.fixture
def qp_prediction():
    return {"Car-1": {"c6/B2": [12650, 12721], "c6/N77": [12663, 12739], "c1/B13": [12576, 12655], "c7/B13": [12649, 12697], "c5/B13": [12592, 12688]}}


@pytest.fixture
def ts_to_qp():
    return '{"UEPredictionSet": ["Car-1"]}'


@pytest.fixture
def qp_train():
    return "c6/B2"
