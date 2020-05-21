.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0
.. Copyright (C) 2020 AT&T Intellectual Property

QoE Predictor Overview
======================

QP is an Xapp in the Traffic Steering O-RAN use case.  There are four total Xapps:

#. Traffic steering, which sends "prediction requests" to QP Driver (this)
#. QP Driver (this) which fetches data from SDL[4] on behalf of traffic steering, both UE Data and Cell Data, merges that data together, then sends off the data to the QP Predictor
#. QP Predictor which predicts (?) and sends that prediction back to Traffic Steering
#. KPIMONN populates SDL in the first place.

Expected Input
--------------

The QP Xapp expects a prediction-request JSON message via RMR with the following structure::

  {
    "predictionUE": "UEId1",
    "ueMeasurements" :
      { "servingCellId" : "CID2",
        "measTimestampUePrbUsage" : TS1,
        "measPeriodUePrbUsage" : Int,
        "uePrbUsageDL" : Int,
        "uePrbUsageUL" : Int,
        "measTimestampUePdcpBytes" : TS2,
        "measPeriodUePdcpByes" : Int,
        "uePdcpBytesDL": Int,
        "uePdcpBytesUL" : Int
      },
    "cellMeasurements" : [
      {
        "cellId" : "CID2",
        "measTimestampPrbAvailable" : TS,
        "measPeriodPrbAvailable" : Int,
        "prbAvailableDL" : Int,
        "prbAvailableUL" : Int,
        "measTimestampPdcpBytes" : TS,
        "measPeriodPdcpBytes" : Int,
        "pdcpBytesDL" : 30000000,
        "pdcpBytesUL" : 5000000,
        "measTimestampRf" : TS,
        "measPeriodRf" : Int,
        "rfMeasurements" : {
          "rsrp": Int,
          "rsrq": Int,
          "rsSinr": Int
       }
     },
     {
       "cellId" : "CID1",
       "measTimestampPrbAvailable" : TS,
       "measPeriodPrbAvailable" : Int,
       "prbAvailableDL" : Int,
       "prbAvailableUL" : Int,
       "measTimestampPdcpBytes" : TS,
       "measPeriodPdcpBytes" : Int,
       "pdcpBytesDL" : 10000000,
       "pdcpBytesUL" : 2000000,
       "measTimestampRf" : TS,
       "measPeriodRf" : Int,
       "rfMeasurements" : {
         "rsrp": Int,
         "rsrq": Int,
         "rsSinr": Int
       }
     },
     {
       "cellId" : "CID3",
       "measTimestampPrbAvailable" : TS,
       "measPeriodPrbAvailable" : Int,
       "prbAvailableDL" : Int,
       "prbAvailableUL" : Int,
       "measTimestampPdcpBytes" : TS,
       "measPeriodPdcpBytes" : Int,
       "pdcpBytesDL" : 50000000,
       "pdcpBytesUL" : 4000000,
       "measTimestampRf" : TS,
       "measPeriodRf" : Int,
       "rfMeasurements" : {
         "rsrp": Int,
         "rsrq": Int,
         "rsSinr": Int
       }
     }
    ]
  }


Expected Output
---------------

The QP Xapp should send a prediction for both downlink and uplink throughput
as a JSON message via RMR with the following structure::

  {
    "UEId1": {
      "CID1" : [10000000,2000000],
      "CID2" : [30000000,5000000],
      "CID3" : [50000000,4000000]
    }
  }


