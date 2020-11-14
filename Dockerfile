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
FROM python:3.8-alpine

# RMR setup
RUN mkdir -p /opt/route/
# copy rmr files from builder image in lieu of an Alpine package
COPY --from=nexus3.o-ran-sc.org:10002/o-ran-sc/bldr-alpine3-rmr:4.0.5 /usr/local/lib64/librmr* /usr/local/lib64/
# rmr_probe replaced health_ck
COPY --from=nexus3.o-ran-sc.org:10002/o-ran-sc/bldr-alpine3-rmr:4.0.5 /usr/local/bin/rmr* /usr/local/bin/
ENV LD_LIBRARY_PATH /usr/local/lib/:/usr/local/lib64
COPY tests/fixtures/local.rt /opt/route/local.rt
ENV RMR_SEED_RT /opt/route/local.rt

# Need to add Alpine edge to get the ML libraries like scikit-learn
RUN echo "http://dl-8.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories

# sdl needs gcc
RUN apk update && apk add gcc musl-dev py3-scikit-learn

# Install
COPY setup.py /tmp
COPY LICENSE.txt /tmp/
COPY qp/ /tmp/qp
RUN pip install /tmp

# Run
ENV PYTHONUNBUFFERED 1
CMD run-qp.py
