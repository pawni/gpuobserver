import paramiko
import os
from datetime import datetime, timedelta

ssh = paramiko.SSHClient()

# be careful to change this if you don't trust to add the hostkeys automatically
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# read ssh credentials from environment
key = os.environ.get('GPUMONITOR_PASS', None)
user = os.environ.get('GPUMONITOR_USER', None)
if user is None:
    raise ValueError('username for SSH is not set')

# interval to iterate through servers
update_interval = timedelta(seconds=30)

# file to write cache to
cache_file = 'cache.pkl'

# fill in your gpu servers here
servers = [
    'gpuserver1',
    'gpuserver2',
]
