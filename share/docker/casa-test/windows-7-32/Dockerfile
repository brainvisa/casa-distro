# Dockerfile for image cati/brainvisa-test:windows-7-32

FROM ubuntu:14.04

RUN dpkg --add-architecture i386  && apt-get update && apt-get install -q -y software-properties-common && add-apt-repository -y ppa:ubuntu-wine/ppa && apt-get update && apt-get upgrade -y && apt-get install --no-install-recommends -y \
    xvfb \
    libx11-xcb1 \
    libfontconfig1 \
    sudo \
    libxrender1 \
    libglib2.0-0 \
    libxi6 \
    libp11-kit-gnome-keyring:i386 \
    libglu1-mesa:i386 \
    libglu1:i386 \
    libgl1-mesa-glx:i386 \
    libudev1:i386 \
    libcgmanager0:i386 \
    wine1.8-i386 \
    winetricks \
    wget \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
# delete all the apt list files since they're big and get stale quickly

# copy a software-only mesa libGL in /usr/local/lib
COPY libGL.so.1 /usr/local/lib/libGL.so.1
COPY libglapi.so.0 /usr/local/lib/libglapi.so.0
RUN ldconfig

COPY entrypoint /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD []
