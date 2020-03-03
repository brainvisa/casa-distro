# Dockerfile for image cati/brainvisa-test:ubuntu-18.04

FROM ubuntu:18.04

# Copy a software-only mesa libGL into /usr/local/lib. We copy this library
# manually because there seems to be no system package that provides a libGL
# which *only* does software rendering. We need such a lib to be used as a
# fallback, when 'singularity run --nv' loads a non-functional Nvidia libGL
# (e.g. when the calling user does not have the required permissions on
# /dev/nvidia*, such as when running over SSH).
COPY libGL.so.1 /usr/local/lib/libGL.so.1
COPY libglapi.so.0 /usr/local/lib/libglapi.so.0

COPY entrypoint /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint

COPY install.sh /casa/install.sh
RUN sh /casa/install.sh
RUN rm /casa/install.sh

ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD []
