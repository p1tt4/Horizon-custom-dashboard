FROM ubuntu:latest
RUN apt update && \
	apt -y dist-upgrade && \
	apt install -y apt-utils \
	tzdata

# these two command works if they are run separately
RUN	apt install -y python-openstackclient \
    nano \
    ansible \
    mysql-client \
    python-pip \
    default-libmysqlclient-dev \
    inetutils-ping

RUN pip install MySQL-python

RUN apt -y install keystone \
    apache2 \
    libapache2-mod-wsgi


ADD entrypoint.sh /
ADD playbook.yml /

ENV OS_USERNAME admin
ENV OS_PASSWORD secret
ENV OS_PROJECT_NAME admin
ENV OS_USER_DOMAIN_NAME Default
ENV OS_PROJECT_DOMAIN_NAME Default
ENV OS_AUTH_URL http://controller:5000/v3
ENV OS_IDENTITY_API_VERSION 3


#ENTRYPOINT [ "/entrypoint.sh" ]

CMD /bin/sh entrypoint.sh && tail -f /dev/null
