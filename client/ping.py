import platform
import subprocess

"""
Currently unused code. It was used to check connection to router/website in case of unavailability of main server.
"""

def ping(host, network_timeout=3):
    """
    Send a ping packet to the specified host, using the system "ping" command.
    Source from: https://stackoverflow.com/a/48767169/2187426
    :param str host: IP address or hostname (website address) as ping target.
    :param int network_timeout: Number of seconds to wait before timeout.
    :returns: True if target responded before timeout, False otherwise.
    """
    
    args = [
        'ping'
    ]

    platform_os = platform.system()

    if platform_os == 'Windows':
        args.extend(['-n', '1'])
        args.extend(['-w', str(network_timeout * 1000)])
    elif platform_os in ('Linux', 'Darwin'):
        args.extend(['-c', '1'])
        args.extend(['-W', str(network_timeout)])
    else:
        raise NotImplementedError('Unsupported OS: {}'.format(platform_os))

    args.append(host)

    try:
        if platform_os == 'Windows':
            output = subprocess.run(args, check=True, universal_newlines=True).stdout

            if output and 'TTL' not in output:
                return False
        else:
            subprocess.run(args, check=True)

        return True
    
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False