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


def _debian_8(hostname=None, ssh_pub_key=None):
    """
    Deploys a new Debian 8 Cloud At Cost server.
    """
    # fix crappy, broken cloud at cost setup
    run('echo 600 > /sys/block/sda/device/timeout')
    run('echo 600 > /sys/block/sr0/device/timeout')
    put('debian_8/etc/rc.local', '/etc/rc.local')
    # configure local time
    run('ln -sf /usr/share/zoneinfo/Etc/UTC /etc/localtime')
    run('dpkg-reconfigure -f noninteractive tzdata')
    # configure hostname
    sed = 'sed -i -e "s:localhost:{}:g" /etc/hostname'.format(hostname)
    run(sed)
    # software upgrade
    put('debian_8/etc/apt/sources.list', '/etc/apt/sources.list')
    run('echo "deb http://ftp.debian.org/debian jessie-backports main" > /etc/apt/sources.list.d/backports.list')
    run('apt update')
    with shell_env(APT_LISTCHANGES_FRONTEND='none'):
        run('apt dist-upgrade -y')
    # install some extra stuff
    run('apt install -y login-duo silversearcher-ag htop firejail tmux unattended-upgrades sudo git irssi')
    # configure ssh
    _ssh_config('debian_8', ssh_pub_key)
    # and reboot!
    run('reboot &')
    pass


def main():
    """
    Main function.
    """
    args = _parse_args()
    if args.type == 'debian_8':
        _debian_8(args.hostname, args.ssh_pub_key.name)
    else:
        exit('Unkown server distribution type.')


if __name__ == '__main__':
    main()
