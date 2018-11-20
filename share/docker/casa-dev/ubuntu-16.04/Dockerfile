# Dockerfile for image cati/casa-dev:ubuntu-16.04

FROM cati/casa-test:ubuntu-16.04 

COPY environment.sh /casa/environment.sh
COPY build_netcdf.sh /tmp/build_netcdf.sh
COPY svn.secret /casa/conf/svn.secret
COPY svn /usr/local/bin/svn

COPY install.sh /casa/install.sh
RUN sh /casa/install.sh
RUN rm /casa/install.sh
