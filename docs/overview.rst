.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property
.. Copyright (C) 2021 HCL Technologies Limited.

QoE Predictor Overview
======================

QoE Predictor (QP) is an Xapp in the Traffic Steering O-RAN use case,
which uses the following Xapps:

#. Traffic Steering, which sends prediction requests to QP.
#. QoE Predictor, which predicts and sends that prediction back to Traffic Steering
#. KPIMONN, which populates UE and Cell metrics into the influxdb.

Expected Input
--------------

The QP Xapp expects a prediction-request JSON message via RMR with the following structure::
{"UEPredictionSet": ["Car-1"]}

Expected Output
---------------

The QP Xapp should send a prediction for both downlink and uplink throughput
as a JSON message via RMR with the following structure::

 {"Car-1":{
 "c6/B2": [12650, 12721],
 "c6/N77": [12663, 12739],
 "c1/B13": [12576, 12655],
 "c7/B13": [12649, 12697],
 "c5/B13": [12592, 12688]
 }}
