# This file is used for building the image Docker. At the moment a separate
# build_image.py file is used to support Singularity and VirtualBox, *please*
# keep these files synchronized so that they perform exactly the same
# installation steps.

FROM ubuntu:18.04

# Use a minimal UTF-8-aware locale.
ENV LANG=C.UTF-8

COPY install_apt_dependencies.sh \
     build_dependencies.sh \
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
          /tmp/build_dependencies.sh \
          /tmp/install_pip_dependencies.sh \
          /tmp/install_compiled_dependencies.sh \
          /tmp/build_netcdf.sh \
          /tmp/build_sip_pyqt.sh \
          /tmp/cleanup_build_dependencies.sh

COPY entrypoint /usr/local/bin/entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD []
