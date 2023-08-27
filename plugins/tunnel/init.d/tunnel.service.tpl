
[Unit]
Description=Tunnel Process Manager
After=network.target

[Service]
Type=forking
ExecStart={$SERVER_PATH}/tunnel/init.d/tunnel start
ExecStop={$SERVER_PATH}/tunnel/init.d/tunnel stop
RemainAfterExit=yes


[Install]
WantedBy=multi-user.target
