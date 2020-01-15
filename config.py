import paramiko
import os
from datetime import datetime, timedelta
import re

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

# process filter
process_filter = re.compile(r'.*')

def update_config(file_path):
    global cache_file, process_filter, servers, update_interval
    import json
    with open(file_path, 'r') as f:
        new_config = json.load(f)

    if 'cache_file' in new_config.keys():
        cache_file = new_config['cache_file']

    if 'servers' in new_config.keys():
        servers = new_config['servers']
    
    if 'update_interval' in new_config.keys():
        update_interval = timedelta(seconds=new_config['update_interval'])

    if 'process_filter' in new_config.keys():
        process_filter = re.compile(new_config['process_filter'])
