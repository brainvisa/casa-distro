# Dockerfile for image cati/brainvisa-test:windows-7-32

FROM ubuntu:14.04

#ENV WINEARCH=win32
ENV WINEPREFIX=/casa/wine
ENV WINEDEBUG=-all

RUN mkdir -p /casa
RUN dpkg --add-architecture i386 \
  && apt-get update \
  && apt-get install -q -y software-properties-common \
  && add-apt-repository -y ppa:ubuntu-wine/ppa \
  && apt-get update \
  && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
    xvfb \
    libx11-xcb1 \
    libfontconfig1 \
    sudo \
    libxrender1 \
    libglib2.0-0 \
    libxi6 \
    libp11-kit-gnome-keyring:i386 \
    libp11-kit-gnome-keyring:amd64 \
    libglu1-mesa:i386 \
    libglu1:i386 \
    libgl1-mesa-glx:i386 \
    libudev1:i386 \
    libcgmanager0:i386 \
    wine1.8-i386 \
    wine1.8 \
    wine-gecko2.34:i386 \
    wine-gecko2.34 \
    wine-mono4.5.4 \
    winetricks \
    wget \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
# delete all the apt list files since they're big and get stale quickly

# Install base wine packages
RUN wine msiexec /i /usr/share/wine/gecko/wine_gecko-2.34-x86_64.msi /L*v gecko-2.34-install.log ALLUSERS=1 \
    && wine msiexec /i /usr/share/wine/mono/wine-mono-4.5.4.msi /L*v mono-4.5.4-install.log ALLUSERS=1

# Update wine configuration to match windows 7 version
RUN wineboot -u \
    && wineserver -w \
    && sed -i 's/"CSDVersion"="Service Pack 2"/"CSDVersion"="Service Pack 1"/g' ${WINEPREFIX}/system.reg \
    && sed -i 's/"CurrentBuildNumber"="3790"/"CurrentBuildNumber"="7601"/g' ${WINEPREFIX}/system.reg \
    && sed -i 's/"CurrentVersion"="5.2"/"CurrentVersion"="6.1"/g' ${WINEPREFIX}/system.reg \
    && sed -i 's/"ProductName"="Microsoft Windows XP"/"ProductName"="Microsoft Windows 7"/g' ${WINEPREFIX}/system.reg \
    && sed -i 's/"CSDVersion"=dword:00000200/"CSDVersion"=dword:00000100/g' ${WINEPREFIX}/system.reg
  
# copy a software-only mesa libGL in /usr/local/lib
COPY libGL.so.1 /usr/local/lib/libGL.so.1
COPY libglapi.so.0 /usr/local/lib/libglapi.so.0
RUN ldconfig

COPY entrypoint /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD []
