# A FROM line must be present but is ignored. It will be overridden by the --image-stream parameter in the buildConfig
FROM centos/python-27-centos7

# Temporarily switch to root user to install packages
USER root

# Install all yum repos we need
COPY RPM-GPG-KEY-* /etc/pki/rpm-gpg/
COPY *.repo /etc/yum.repos.d/

# Install whatever is necessary
RUN  yum install --assumeyes python-devel gcc libxml2 libxml2-devel libxslt \
     libxslt-devel mariadb-devel-5.5.56-2.el7 mariadb-libs-5.5.56-2.el7 python-lxml-3.2.1-4.el7 \
     MySQL-python-1.2.5-1.el7 cert-soc-lib && yum clean all


# Copy the installed yum packages into the env's site packages. Dirty but it works :)
RUN cp -Rs /usr/lib/python2.7/site-packages/* /opt/app-root/lib/python2.7/site-packages/ \
    && chown -R 1001 /opt/app-root/lib/python2.7/ && chown -R 1001 /usr/lib/python2.7/


# Make sure the final image runs as unprivileged user
USER 1001