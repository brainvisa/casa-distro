# Dockerfile for image cati/casa-dev:ubuntu-16.04

FROM cati/casa-test:ubuntu-16.04 

COPY environment.sh /casa/environment.sh
COPY build_netcdf.sh /tmp/build_netcdf.sh

COPY svn.secret /casa/conf/svn.secret
COPY svn /usr/local/bin/svn
COPY askpass-bioproj.sh /usr/local/bin/askpass-bioproj.sh

# install python and pip to get apt-mirror-updater
# in order to select an efficient debian mirror.
# (try installing up to 5 times if the default server sometimes disconnects)
RUN for trial in 1 2 3 4 5; do apt-get update && break; done \
 && for trial in 1 2 3 4 5; do DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip && break; done \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
RUN pip install apt-mirror-updater
# setup best mirror in /etc/apt/sources.list
RUN apt-mirror-updater -a

COPY install_1.sh /casa/install_1.sh
RUN sh /casa/install_1.sh

COPY install_2.sh /casa/install_2.sh
RUN sh /casa/install_2.sh

RUN rm /casa/install_1.sh
RUN rm /casa/install_2.sh
