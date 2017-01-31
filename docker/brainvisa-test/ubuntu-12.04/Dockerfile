# Dockerfile for image cati/brainvisa-test:ubuntu-12.04

FROM ubuntu:12.04

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    xvfb \
    libx11-xcb1 \
    libfontconfig1 \
    sudo \
  && apt-get clean

RUN groupadd brainvisa && useradd -g brainvisa -G sudo -p "" -ms /bin/bash brainvisa
COPY entrypoint /usr/local/bin/entrypoint
USER brainvisa
WORKDIR /home/brainvisa
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD []
