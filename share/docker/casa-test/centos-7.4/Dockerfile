# Dockerfile for image cati/brainvisa-test:centos-7.4

FROM centos:7.4.1708

# Install system dependencies
RUN yum -y update --security && \
    yum -y install \
    xorg-x11-server-Xvfb.x86_64 \
    libX11 \
    fontconfig \
    sudo \
    Xrender \
    glib2 \
    libXi \
    wget \
  && yum clean all
# delete all the yum list files since they're big and get stale quickly

# copy a software-only mesa libGL in /usr/local/lib
COPY libGL.so.1 /usr/local/lib/libGL.so.1
COPY libglapi.so.0 /usr/local/lib/libglapi.so.0
RUN ldconfig

# allow sudo yum without password
RUN echo "ALL     ALL=(root)     NOPASSWD:      /usr/bin/yum, /usr/bin/rpm, /usr/bin/rpmquery" > /etc/sudoers.d/90_sudoers-yum
RUN chmod 440 /etc/sudoers.d/90_sudoers-yum

# create casa directories for singularity compatibility            
RUN mkdir -p /casa/pack \
             /casa/install \
             /casa/tests

RUN chmod 777 /casa \
              /casa/pack \
              /casa/install \
              /casa/tests
              
COPY entrypoint /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD []
