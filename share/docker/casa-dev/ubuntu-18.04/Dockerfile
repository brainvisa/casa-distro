# Dockerfile for image cati/casa-dev:ubuntu-18.04

FROM cati/casa-run:ubuntu-18.04

COPY install_apt_dev_dependencies.sh /tmp/
RUN /tmp/install_apt_dev_dependencies.sh

COPY install_pip_dev_dependencies.sh /tmp/
RUN /tmp/install_pip_dev_dependencies.sh

COPY install_compiled_dev_dependencies.sh /tmp/
COPY build_sip_pyqt.sh /tmp/build_sip_pyqt.sh
RUN /tmp/install_compiled_dev_dependencies.sh

COPY install_casa_dev_components.sh /tmp/
COPY environment.sh /casa/environment.sh
COPY svn.secret /casa/conf/svn.secret
COPY svn /usr/local/bin/svn
COPY askpass-bioproj.sh /usr/local/bin/askpass-bioproj.sh
RUN /tmp/install_casa_dev_components.sh

# Used to generate a list of packages to include in the casa-run image (see
# share/docker/casa-run/.../install_apt_dependencies.sh).
COPY list-shared-libs-paths.sh /casa/list-shared-libs-paths.sh

RUN rm -f /casa/install_apt_dev_dependencies.sh \
          /casa/build_sip_pyqt.sh \
          /casa/install_pip_dev_dependencies.sh \
          /casa/install_compiled_dev_dependencies.sh \
          /casa/install_casa_dev_components.sh
