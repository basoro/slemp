FROM debian:10.12-slim

STOPSIGNAL SIGRTMIN+3

RUN rm -f /lib/systemd/system/multi-user.target.wants/* \
  /etc/systemd/system/*.wants/* \
  /lib/systemd/system/local-fs.target.wants/* \
  /lib/systemd/system/sockets.target.wants/*udev* \
  /lib/systemd/system/sockets.target.wants/*initctl* \
  /lib/systemd/system/sysinit.target.wants/systemd-tmpfiles-setup* \
  /lib/systemd/system/systemd-update-utmp*

RUN apt update -y && \
	apt install -y devscripts && \
	apt install -y curl wget zip unzip && \
  apt-get install -y locales && \
  localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 && \
  locale-gen en_US.UTF-8 && \
  export LC_ALL=en_US.UTF-8 && \
  export LANG=en_US.UTF-8 && \
  export LANGUAGE=en_US.UTF-8 && \
  localedef -i en_US -f UTF-8 en_US.UTF-8 && \
  curl --insecure -fsSL https://basoro.id/slemp.sh | bash && \
  cd /home/slemp/server/panel/ && \
  /home/slemp/server/panel/bin/python tools.py username username && \
  cd /home/slemp/server/panel/ && \
  /home/slemp/server/panel/bin/python tools.py panel password && \
  cd /home/slemp/server/panel/ && \
  echo '7200' > data/port.pl && \
  cd /home/slemp/server/panel/ && \
  echo 'login' > data/admin_path.pl && \
  slemp stop 

ADD ./start.sh /start.sh
ADD start.service /usr/lib/systemd/system/start.service
#RUN systemctl enable start

CMD [ "/lib/systemd/systemd", "log-level=info", "unit=sysinit.target" ]

EXPOSE 7200 80 443 888

VOLUME [ "/home/slemp" ]
