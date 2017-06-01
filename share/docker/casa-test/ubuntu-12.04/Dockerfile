# Dockerfile for image cati/brainvisa-test:ubuntu-12.04

FROM ubuntu:12.04

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install --no-install-recommends -y \
    xvfb \
    libx11-xcb1 \
    libfontconfig1 \
    sudo \
    libxrender1 \
    libglib2.0-0 \
    libxi6 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
# delete all the apt list files since they're big and get stale quickly

COPY entrypoint /usr/local/bin/entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD []
