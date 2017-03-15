# Dockerfile for image cati/brainvisa-opensource:ubuntu-12.04-trunk

FROM cati/brainvisa-devbase:ubuntu-12.04 

COPY svn.secret /etc/brainvisa/svn.secret
COPY bv_maker.cfg /etc/brainvisa/bv_maker.cfg
COPY svn /home/brainvisa/bin/svn

USER root
RUN chown -R brainvisa:brainvisa /etc/brainvisa
RUN mkdir /repository
RUN chown brainvisa:brainvisa /repository
USER brainvisa

ENV PATH="/home/brainvisa/bin:${PATH}"
RUN mkdir ~/.brainvisa && \
    ln -s /etc/brainvisa/bv_maker.cfg ~/.brainvisa/bv_maker.cfg

RUN /home/brainvisa/bin/svn export https://bioproj.extra.cea.fr/neurosvn/brainvisa/development/brainvisa-cmake/branches/bug_fix /tmp/brainvisa-cmake
WORKDIR /tmp/brainvisa-cmake
RUN cmake -DCMAKE_INSTALL_PREFIX=. .
RUN make install
RUN /tmp/brainvisa-cmake/bin/bv_env_host bv_maker sources
RUN /tmp/brainvisa-cmake/bin/bv_env_host bv_maker configure
RUN /tmp/brainvisa-cmake/bin/bv_env_host bv_maker build
RUN /tmp/brainvisa-cmake/bin/bv_env_host bv_maker doc
RUN rm -Rf /tmp/brainvisa-cmake

WORKDIR /home/brainvisa
VOLUME /etc/brainvisa
VOLUME /repository

ENTRYPOINT ["/home/brainvisa/build/bin/bv_env"]
CMD []
