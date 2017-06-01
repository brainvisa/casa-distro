# Dockerfile for image cati/brainvisa-test:ubuntu-16.04

FROM mageia:5

# Install system dependencies
RUN urpmi --no-recommends --auto \
    lib64xi6 \
    lib64freetype6 \
    lib64xrender1 \
    x11-server-xvfb \
    lib64fontconfig1 \
    sudo \
    lib64xcb1 \
    lib64dbus1_3 \
    lib64glib2.0_0 \
    lib64sm6 \
    lib64xt6

COPY entrypoint /usr/local/bin/entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD []
