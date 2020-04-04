FROM ubuntu:18.04

# Use a minimal UTF-8-aware locale.
ENV LANG=C.UTF-8

COPY install_apt_dependencies.sh \
     neurodebian.sources.list \
     neurodebian-key.gpg \
     /tmp/
RUN /tmp/install_apt_dependencies.sh

COPY install_pip_dependencies.sh /tmp/
RUN /tmp/install_pip_dependencies.sh

COPY install_compiled_dependencies.sh \
     build_netcdf.sh \
     build_sip_pyqt.sh \
     /tmp/
RUN /tmp/install_compiled_dependencies.sh

COPY cleanup_build_dependencies.sh /tmp/
RUN /tmp/cleanup_build_dependencies.sh


RUN rm -f /tmp/neurodebian-key.gpg \
          /tmp/neurodebian.sources.list \
          /tmp/install_apt_dependencies.sh \
          /tmp/install_pip_dependencies.sh \
          /tmp/install_compiled_dependencies.sh \
          /tmp/build_netcdf.sh \
          /tmp/build_sip_pyqt.sh \
          /tmp/cleanup_build_dependencies.sh


# Copy a software-only mesa libGL into /usr/local/lib. We copy this library
# manually because there seems to be no system package that provides a libGL
# which *only* does software rendering. We need such a lib to be used as a
# fallback, when 'singularity run --nv' loads a non-functional Nvidia libGL
# (e.g. when the calling user does not have the required permissions on
# /dev/nvidia*, such as when running over SSH).
COPY libGL.so.1 /usr/local/lib/libGL.so.1
COPY libglapi.so.0 /usr/local/lib/libglapi.so.0

COPY entrypoint /usr/local/bin/entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD []
