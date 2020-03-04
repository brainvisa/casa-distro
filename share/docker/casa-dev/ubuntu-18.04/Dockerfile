# Dockerfile for image cati/casa-dev:ubuntu-18.04

FROM cati/casa-test:ubuntu-18.04

COPY environment.sh /casa/environment.sh

COPY build_netcdf.sh /tmp/build_netcdf.sh
COPY build_sip_pyqt.sh /tmp/build_sip_pyqt.sh

COPY svn.secret /casa/conf/svn.secret
COPY svn /usr/local/bin/svn
COPY askpass-bioproj.sh /usr/local/bin/askpass-bioproj.sh

COPY install_1.sh /casa/install_1.sh
RUN sh /casa/install_1.sh

COPY install_2.sh /casa/install_2.sh
RUN sh /casa/install_2.sh

COPY install_3.sh /casa/install_3.sh
RUN sh /casa/install_3.sh

RUN rm -f /casa/install_1.sh /casa/install_2.sh /casa/install_3.sh
