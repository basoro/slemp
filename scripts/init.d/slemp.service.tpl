[Unit]
Description=slemp-panel daemon
After=network.target

[Service]
Type=simple
WorkingDirectory={$SERVER_PATH}
EnvironmentFile={$SERVER_PATH}/scripts/init.d/service.sh
ExecStart=gunicorn -c setting.py app:app
ExecStop=kill -HUP $MAINID
ExecReload=kill -HUP $MAINID
KillMode=process
Restart=on-failure

[Timer]
# Restart every morning
OnCalendar=*-*-* 03:30:00
Unit=slemp.service

[Install]
WantedBy=multi-user.target
