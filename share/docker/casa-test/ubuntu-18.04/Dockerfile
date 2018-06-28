# Dockerfile for image cati/brainvisa-test:ubuntu-18.04

FROM ubuntu:18.04

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install --no-install-recommends -y \
    xvfb \
    libx11-xcb1 \
    libfontconfig1 \
    libdbus-1-3 \
    sudo \
    libxrender1 \
    libglib2.0-0 \
    libxi6 \
    wget \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
# delete all the apt list files since they're big and get stale quickly

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
