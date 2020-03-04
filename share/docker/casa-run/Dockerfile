FROM cati/casa-test:ubuntu-18.04

# TODO keep this?
COPY build_netcdf.sh /tmp/build_netcdf.sh
COPY build_sip_pyqt.sh /tmp/build_sip_pyqt.sh

COPY install_runtime_dependencies.sh /tmp
RUN /tmp/install_runtime_dependencies.sh
