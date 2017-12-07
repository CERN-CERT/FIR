# A FROM line must be present but is ignored. It will be overridden by the --image-stream parameter in the buildConfig
FROM centos/python-27-centos7

# Temporarily switch to root user to install packages
USER root
# Install whatever is necessary. For brevity we use --nogpgcheck, don't do this in real applications!
RUN echo -e '[cc7-cernonly]\nname=CC7-CERNOnly\nbaseurl=http://linuxsoft.cern.ch/cern/centos/7/cernonly/x86_64' > /etc/yum.repos.d/cc7-cernonly.repo \
    && yum install --assumeyes --nogpgcheck python-devel gcc libxml2 libxml2-devel libxslt \
     libxslt-devel mariadb-devel-5.5.56-2.el7 mariadb-libs-5.5.56-2.el7 python-lxml-3.2.1-4.el7 \
     MySQL-python-1.2.5-1.el7

# Make sure the final image runs as unprivileged user
USER 1001