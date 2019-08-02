# Dockerfile for image cati/brainvisa-test:ubuntu-18.04

FROM ubuntu:18.04

# copy a software-only mesa libGL in /usr/local/lib
COPY libGL.so.1 /usr/local/lib/libGL.so.1
COPY libglapi.so.0 /usr/local/lib/libglapi.so.0

COPY entrypoint /usr/local/bin/entrypoint

COPY install.sh /casa/install.sh
RUN sh /casa/install.sh
RUN rm /casa/install.sh

ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD []
