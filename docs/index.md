# Miner Watchdog
This repository contains source code for client part of a Python application for monitoring [Claymore miner](https://bitcointalk.org/index.php?topic=1433925.0). Basically it periodically connects to miner, gets hashrate and other data and sends them to monitoring server.

With some tweaks (installing new Python and two Python packages), this software may run on the miner itself. In this case, it will automatically restart it on low hashrate or internet problems.

## Installing (on Linux)

Copy files to miner machine.

Edit `/etc/rc.local` so `client.py` is automatically executed when computer boots up. Change `<full_path>` to full path to client and log directory respectively. Change `<user>` to user name with rights to restart a computer (on EthOS, use `ethos`).

    su - c "python3.5 <full_path>/client.py > <full_path>/logs/output.txt 2>&1 &" - <user>

Install pip:

    curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py

and then run:

    python3.5 get-pip.py

Install `twisted` and `requests` packages

    pip3.5 install twisted requests

If you haven't done it yet, change timezone. Full list of valid values may be listed with `timedatectl list-timezones`.

    timedatectl set-timezone <TimeZone>

In the admin section of monitoring server, generate a `secret` for this client.

Allow monitoring in claymore's configuration. Add following parameter to it's configuration with selected port.

    -mport <PORT>
    
Edit file `config.ini` and fill everything with valid values.

Restart computer.

## Configuration

Each client comes with a `config.ini` file for configuration. Full list of keys follows:

### [server]
All keys related to server belongs under this header.

- **address** - Full path to monitoring server. Support both HTTP and HTTPS URL.
- **ping** - Hostname or IP address for ping requests. This is used when main server is not available to check whether internet connection is working fine. Note: This key is deprecated since v0.0.2.

### [client]
- **name** - Name of the client. Use this only as display name on the server. For identification, use `secret` key.
- **hashrate** - Minimal hashrate in H/s. Everything below this threshold triggers miner restart.
- **interval** - Number of seconds between each hashrate check (and upload to the server).
- **host** - IP address or hostname of computer claymore miner is running on. If you are running watchdog on the computer with claymore, set it to `localhost`.
- **port** - Port on which claymore will listen. This value is the same as in `-mport` parameter of Claymore.
- **secret** - Unique string for identification of each miner.

### Example Configuration

    [server]
    address=https://api.server.com

    [client]
    name=Miner
    hashrate=123456789
    interval=300
    port=36879
    host=localhost
    secret=f65sad98a7we9f84asd65678hjkj

