# Dockerfile for image sandbox.brainvisa.info/brainvisa-standard:ubuntu-16.04-trunk

FROM cati/brainvisa-opensource:ubuntu-16.04-trunk 

COPY svn.secret /etc/brainvisa/svn.secret
ARG SVN_USERNAME
ARG SVN_PASSWORD

COPY bv_maker.cfg /home/brainvisa/.brainvisa/bv_maker.cfg
COPY svn /home/brainvisa/bin/svn

USER brainvisa

ENV PATH="/home/brainvisa/bin:/home/brainvisa/build/bin:${PATH}"

RUN bv_maker sources
RUN bv_maker configure
RUN bv_maker build
RUN bv_maker doc

RUN rm /etc/brainvisa/svn.secret

WORKDIR /home/brainvisa
VOLUME /etc/brainvisa
VOLUME /repository

ENTRYPOINT ["/home/brainvisa/build/bin/bv_env"]
CMD []
