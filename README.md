### SLEMP Panel
Simple Linux Engine-X (Openresty) MySQL PHP-FPM. Linux panel for VPS (or Dedicated Server) inspired by Pagoda Panel. I imitate the Layui based interface and writing the plugins with my own way. The plugins is independent, simple and light.

#### Main Plugin
- OpenResty - Lightweight, occupies less memory, and has strong concurrency capabilities.
- PHP[52-82] - PHP is the best programming language in the world.
- MySQL - A relational database management system with master-slave replication panel.
- phpMyAdmin - Famous web-side MySQL management tool.
- Swap - Virtual memory for linux to increase server performance.
- Rsyncd - Universal synchronization service.

#### Support OS
- MacOSX
- Centos
- Debian
- Ubuntu
- Raspberry Pi
- Fedora
- Alma Linux
- Amazon Linux
- Rocky Linux
- Arch Linux
- Open SUSE

### Install

There are two ways to install SLEMP Panel: using the automated installation script or manually from the source.

**Method 1: Automated Installation (Recommended for Linux)**
```bash
curl --insecure -fsSL https://basoro.id/slemp.sh | bash
```

**Method 2: Manual Installation from Source (Recommended for MacOSX / Local Development)**
If you want to install SLEMP Panel in a custom directory (e.g., `~/SLEMP`), you can clone the repository and run the installation script manually. The script dynamically detects your path and sets up the environment accordingly.

```bash
# Clone the repository
git clone https://github.com/your-username/SLEMP.git ~/SLEMP
cd ~/SLEMP/panel

# Run the installation script
bash scripts/install.sh
```

### Usage

Once installed, the SLEMP Panel runs in the background. You can manage the panel service using the command-line interface.

If you installed the panel using the automated script, the `slemp` command is linked globally. If you installed it manually, you can execute the script directly from your installation directory (e.g., `bash scripts/init.d/slemp`).

#### CLI Commands

| Command | Description |
| --- | --- |
| `slemp start` | Starts the SLEMP Panel and background tasks. |
| `slemp stop` | Stops the SLEMP Panel and background tasks. |
| `slemp restart` | Restarts the SLEMP Panel. |
| `slemp status` | Checks the running status of the panel. |
| `slemp default` | Displays the default access information (URLs, Intranet IP, Username, Password). |

*Example output for `slemp default`:*
```text
==================================================================
SLEMP-Panel default info!
==================================================================
SLEMP-Panel-Url-Ipv4: http://198.51.100.1:64448/bhmbjoam 
SLEMP-Panel-Url-Local: http://192.168.1.10:64448/bhmbjoam
username: gjl9ozsp
password: rnwbbp
```

### Uninstallation

SLEMP provides a safe uninstallation script that allows you to cleanly remove the panel from your system. It also includes an interactive option to back up your websites and databases before deletion.

To run the uninstaller:
```bash
bash scripts/uninstall.sh
```

During the uninstallation process, you will be prompted to:
1. Confirm the uninstallation of the SLEMP Panel.
2. Confirm whether you want to delete all server data (plugins, databases, and website files).
3. If deleting server data, whether you want to safely back up your databases and `wwwroot` directories to a separate `backup/` directory first.
