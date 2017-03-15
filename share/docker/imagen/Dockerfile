FROM ubuntu:16.04

ENV LDAP_PASSWORD="ldap_password"
ENV DOMAIN_NAME="imagen5.cea.fr
ENV ORGANIZATION="imagen5"
ENV LDAP_BASE="dc=imagen5,dc=cea,dc=fr"
ENV USER_ACCOUNT=imagen
ENV USER_PASSWORD=openbar
ENV PUBLICATION_CUBE_NAME="imagen"
ENV PUBLICATION_INSTANCE_NAME="imagen_publication"

EXPOSE 8080
EXPOSE 22

RUN apt update && apt upgrade -y && DEBIAN_FRONTEND=noninteractive apt install -y \
    vim \
    git \
    gosu \
    openssh-server \
    slapd \
    ldap-utils \
    phpldapadmin \
    patch \
    python-apt \
    python-pip \
    mercurial gcc \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libpq-dev \
    libgecode-dev \
    postgresql \
    postgresql-plpython-9.5 \
    python-pip \
    python-dev \
    python-lxml \
    pgadmin3 \
    python-virtualenv \
    libjpeg-dev \
    gettext && \
    apt clean

# ssh configuration
RUN mkdir /var/run/sshd
RUN echo 'root:screencast' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# LDAP configuration
RUN echo -e '-e "# Omit OpenLDAP server configuration?\n\
slapd	slapd/no_configuration	boolean	false\n\
# DNS domain name:\n\
slapd	slapd/domain	string	'$DOMAIN_NAME'\n\
# Organization name:\n\
slapd	shared/organization	string	'$ORGANIZATION'\n\
# Administrator password:\n\
slapd	slapd/password1	password	'$LDAP_PASSWORD'\n\
# Confirm password:\n\
slapd	slapd/password2	password	'$LDAP_PASSWORD'\n\
# Database backend to use:\n\
# Choices: BDB, HDB, MDB\n\
slapd	slapd/backend	select	MDB\n\
# Do you want the database to be removed when slapd is purged?\n\
slapd	slapd/purge_database	boolean	true\n\
# Move old database?\n\
slapd	slapd/move_old_database	boolean	true\n\
# Allow LDAPv2 protocol?\n\
slapd	slapd/allow_ldap_v2	boolean	false\n\
' | debconf-set-selections && \
DEBIAN_FRONTEND=noninteractive dpkg-reconfigure slapd -fnoninteractive

# PHPLDAPadmin configuration
RUN echo -e "161c161\n\
< // \$config->custom->appearance['hide_template_warning'] = false;\n\
---\n\
> // \$config->custom->appearance['hide_template_warning'] = true;\n\
300c300\n\
< \$servers->setValue('server','base',array('dc=example,dc=com'));\n\
---\n\
> \$servers->setValue('server','base',array('$LDAP_BASE'));\n\
326c326\n\
< \$servers->setValue('login','bind_id','cn=admin,dc=example,dc=com');\n\
---\n\
> \$servers->setValue('login','bind_id','cn=admin,$LDAP_BASE');\n\
"| patch  /etc/phpldapadmin/config.php -


COPY data/python-cwinstall-1.0.0_Ubuntu_16.04_amd64.deb /tmp
RUN dpkg -i /tmp/python-cwinstall-1.0.0_Ubuntu_16.04_amd64.deb

RUN groupadd $USER_ACCOUNT && useradd -g $USER_ACCOUNT -p "$USER_PASSWORD" -ms /bin/bash $USER_ACCOUNT
COPY data/cw_required /tmp/cw_required

COPY data/xenial_3_20_9.conf /usr/lib/python2.7/dist-packages/cwinstall/config/
USER $USER_ACCOUNT
SHELL ["/bin/bash", "-c"]
RUN echo -e '8\n0 1 2 3 4 5\n' \
  | cwinstall -n $PUBLICATION_INSTANCE_NAME -s /tmp

USER root
RUN locale-gen en_US.UTF-8
COPY postgresql_force_utf8_template.sql /tmp
COPY data/db /tmp/
COPY data/imagen_dump_iteration6.cw /tmp
COPY install_cube_instance /tmp

COPY data/imagen_migration_postcreate.py /tmp
RUN chown -R $USER_ACCOUNT:$USER_ACCOUNT /home/imagen/virtualenvs
RUN gosu postgres service postgresql start && \
    gosu postgres createuser --superuser $USER_ACCOUNT && \
    gosu postgres psql -f /tmp/postgresql_force_utf8_template.sql && \
    mkdir /etc/publication && \
    echo '{"ldap-password": "'$LDAP_PASSWORD'","base-dn": "'$LDAP_BASE'"}' > /etc/publication/ldap_configuration.json && \
    chown $USER_ACCOUNT:$USER_ACCOUNT etc/publication/ldap_configuration.json  && \
    gosu $USER_ACCOUNT /tmp/install_cube_instance && \
    gosu postgres service postgresql stop

USER $USER_ACCOUNT
COPY data/all-in-one.conf.diff /tmp
RUN patch ~/virtualenvs/$PUBLICATION_INSTANCE_NAME/etc/cubicweb.d/$PUBLICATION_INSTANCE_NAME/all-in-one.conf /tmp/all-in-one.conf.diff
RUN cd ~/virtualenvs/$PUBLICATION_INSTANCE_NAME/git/rql_download && \
    git pull && \
    git checkout 11024dcc458fc714886a8440d3e6cae14b20b742
USER root
COPY publication-server /etc/init.d
RUN < /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c${1:-32} > /etc/publication/secret-key && \
    chown $USER_ACCOUNT:$USER_ACCOUNT etc/publication/secret-key
RUN rm -r /tmp/python-cwinstall-1.0.0_Ubuntu_16.04_amd64.deb \
    /tmp/cw_required \
    /tmp/postgresql_force_utf8_template.sql \
    /tmp/db /tmp/imagen_dump_iteration6.cw \
    /tmp/install_cube_instance \
    /tmp/all-in-one.conf.diff

COPY start_container /usr/local/bin/
CMD ["/usr/local/bin/start_container"]
RUN mkdir /tmp/data
VOLUME /tmp/data
