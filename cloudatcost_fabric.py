#!/usr/bin/env python
from argparse import ArgumentParser, FileType
from sys import exit

from fabric.api import env, run
from fabric.context_managers import cd, shell_env
from fabric.operations import put


# root, yay!
env.user = 'root'


def _parse_args():
    """
    Parses command line arguments.
    """
    description = """
    Deploys servers at Cloud At Cost.
    """
    parser = ArgumentParser(description=description)
    parser.add_argument('-k', '--ssh-pub-key', type=FileType('r'), metavar='ssh_pub_key', help='ssh public key to upload to the server to configure', required=True)
    parser.add_argument('-n', '--hostname', type=str, metavar='hostname', help='hostname to give to the server to configure', required=True)
    parser.add_argument('-t', '--type', type=str, metavar='server_type', help='server distribution type to configure', required=True)
    args = parser.parse_args()
    return args


def _ssh_config(server_type, ssh_pub_key):
    """
    Configures ssh access.
    """
    with cd('/root'):
        run('mkdir -p .ssh')
        run('chmod 0700 .ssh')
        put(ssh_pub_key, '.ssh/authorized_keys')
        run('chmod 0600 .ssh/authorized_keys')
    sshd_config = '{}/etc/ssh/sshd_config'.format(server_type)
    put(sshd_config, '/etc/ssh/sshd_config')
    run('rm /etc/ssh/ssh_host_*')
    run('dpkg-reconfigure openssh-server')
    run('cat /etc/ssh/ssh_host_ed25519_key.pub')


def _configure_localtime():
    """
    Configures local time.
    """
    run('ln -sf /usr/share/zoneinfo/Etc/UTC /etc/localtime')
    run('dpkg-reconfigure -f noninteractive tzdata')


def _fix_devices_timeout():
    """
    Fixes crappy, broken cloud at cost disk setup.
    """
    run('echo 600 > /sys/block/sda/device/timeout')
    run('echo 600 > /sys/block/sr0/device/timeout')
    put('debian_8/etc/rc.local', '/etc/rc.local')


def _configure_hostname(server_type, hostname):
    """
    Configures hostname.
    """
    if server_type == 'debian_8':
        sed = 'sed -i -e "s:localhost:{}:g" /etc/hostname'.format(hostname)
    elif server_type == 'ubuntu_14':
        sed = 'sed -i -e "s:ubuntu:{}:g" /etc/hosts /etc/hostname'.format(hostname)
    run(sed)


def _apt_dist_upgrade(options=''):
    """
    Runs apt dist-upgrade.
    """
    run('apt update')
    with shell_env(APT_LISTCHANGES_FRONTEND='none'):
        run('apt dist-upgrade -y {}'.format(options))


def _debian_8(hostname, ssh_pub_key, server_type):
    """
    Deploys a new Debian 8 Cloud At Cost server.
    """
    _fix_devices_timeout()
    _configure_localtime()
    _configure_hostname(server_type, hostname)
    put('debian_8/etc/apt/sources.list', '/etc/apt/sources.list')
    run('echo "deb http://ftp.debian.org/debian jessie-backports main" > /etc/apt/sources.list.d/backports.list')
    _apt_dist_upgrade()
    run('apt install -y login-duo silversearcher-ag htop firejail tmux unattended-upgrades sudo git irssi')
    _ssh_config('debian_8', ssh_pub_key)
    run('reboot &')
    pass


def _remove_user(user=None):
    """
    Removes a specific user access.
    """
    assert(user)
    run('usermod --expiredate 1 {}'.format(user))
    run('deluser --remove-all-files {}'.format(user))


def _ubuntu_14(hostname, ssh_pub_key, server_type):
    """
    Deploys a new Ubuntu 14.04.1 Cloud At Cost server.
    """
    _remove_user('user')
    _fix_devices_timeout()
    _configure_localtime()
    _configure_hostname(server_type, hostname)
    run('echo "deb http://pkg.duosecurity.com/Ubuntu trusty main" > /etc/apt/sources.list.d/duo.list')
    run('curl -s https://duo.com/APT-GPG-KEY-DUO | apt-key add -')
    _apt_dist_upgrade('-o Dpkg::Options::="--force-confold"')
    run('apt install -y login-duo silversearcher-ag htop unattended-upgrades')
    _ssh_config('ubuntu_14', ssh_pub_key)
    run('reboot &')
    pass


def main():
    """
    Main function.
    """
    args = _parse_args()
    if args.type == 'debian_8':
        _debian_8(args.hostname, args.ssh_pub_key.name, 'debian_8')
    elif args.type == 'ubuntu_14':
        _ubuntu_14(args.hostname, args.ssh_pub_key.name, 'ubuntu_14')
    else:
        exit('Unkown server distribution type.')


if __name__ == '__main__':
    main()