# Dockerfile for image cati/brainvisa-test:ubuntu-14.04

FROM ubuntu:14.04

# Use a minimal UTF-8-aware locale.
ENV LANG=C.UTF-8

# Install system dependencies
# WARNING: it is necessary to call apt-get install for each packages to 
# avoid the 101th package issue
RUN apt-get update \
 && apt-get upgrade -y \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y xvfb \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y libx11-xcb1 \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y libfontconfig1 \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y sudo \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y libxrender1 \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y libglib2.0-0 \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y libxi6 \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y wget \
&& DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y x11-utils \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y mesa-utils \
&& DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y tcsh \
&& DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y dc \
&& DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y bc \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
# delete all the apt list files since they're big and get stale quickly

# virtualGL
RUN cd /tmp && wget --no-check-certificate https://sourceforge.net/projects/virtualgl/files/2.6.1/virtualgl_2.6.1_amd64.deb \
  && dpkg -i virtualgl_2.6.1_amd64.deb \
  && rm -f /tmp/virtualgl_2.6.1_amd64.deb

# copy a software-only mesa libGL in /usr/local/lib
COPY libGL.so.1 /usr/local/lib/libGL.so.1
COPY libglapi.so.0 /usr/local/lib/libglapi.so.0
RUN ldconfig

# allow sudo apt without password
RUN echo "ALL     ALL=(root)     NOPASSWD:      /usr/bin/apt, /usr/bin/apt-get, /usr/bin/aptitude" > /etc/sudoers.d/90_sudoers-apt
RUN chmod 440 /etc/sudoers.d/90_sudoers-apt

# create casa directories for singularity compatibility            
RUN mkdir -p /casa/home \
             /casa/pack \
             /casa/install \
             /casa/tests

RUN chmod 777 /casa \
              /casa/home \
              /casa/pack \
              /casa/install \
              /casa/tests
              
COPY entrypoint /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD []
