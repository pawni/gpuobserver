import config
import xml.etree.ElementTree as ET
import pwd
import logging
from datetime import datetime, timedelta
import threading
import pickle
import os
import traceback

logger = logging.getLogger()

# init cache
cache = {
    'users': {},
    'since': datetime.now()
}

# init template
user_template = {'name': '', 'inc': 0, 'time': timedelta(seconds=0.), 'cum_energy': 0., 'cum_util': 0.}

def get_nvidiasmi(ssh):
    # function to get nvidia smi xmls
    _, ssh_stdout, _ = config.ssh.exec_command('nvidia-smi -q -x')

    res = ''.join(ssh_stdout.readlines())
    return ET.fromstring(res)


def get_ps(ssh, pids):
    # function to identify processes running
    pid_cmd = 'ps -o pid= -o ruser= -p {}'.format(','.join(pids))
    _, ssh_stdout, _ = config.ssh.exec_command(pid_cmd)

    res = ''.join(ssh_stdout.readlines())

    return res


def get_users_by_pid(ps_output):
    # function to identify user of a process
    users_by_pid = {}
    if ps_output is None:
        return users_by_pid

    for line in ps_output.strip().split('\n'):
        pid, user = line.split()
        users_by_pid[pid] = user

    return users_by_pid


def update_users(info):
    # updates cache of user usage statistics
    for user, real_user in zip(info['users'], info['real_users']):
        if user not in cache['users']:
            cache['users'][user] = {}
            cache['users'][user].update(user_template)
            cache['users'][user]['name'] = real_user

        cache['users'][user]['inc'] += 1
        cache['users'][user]['time'] += config.update_interval
        pwr_float = float(info['power_draw'][:-2])
        cache['users'][user]['cum_energy'] += pwr_float * config.update_interval.total_seconds() / 3600
        gpu_util = float(info['gpu_util'][:-2])
        cache['users'][user]['cum_util'] += gpu_util


def get_gpu_infos(ssh):
    # collects gpu usage information for a ssh connection  
    nvidiasmi_output = get_nvidiasmi(ssh)
    gpus = nvidiasmi_output.findall('gpu')

    gpu_infos = []
    for idx, gpu in enumerate(gpus):
        model = gpu.find('product_name').text
        power_draw = gpu.find('power_readings').find('power_draw').text
        processes = gpu.findall('processes')[0]
        pids = [process.find('pid').text for process in processes]
        mem = gpu.find('fb_memory_usage').find('total').text
        gpu_util = gpu.find('utilization').find('gpu_util').text
        used_mem = gpu.find('fb_memory_usage').find('used').text
        free = (len(pids) == 0)

        info = {
            'idx': idx,
            'model': model,
            'pids': pids,
            'power_draw': power_draw,
            'free': free,
            'mem': mem,
            'gpu_util': gpu_util,
            'used_mem': used_mem
        }
        
        if free:
            users = []
            real_users = []
        else:
            ps_output = get_ps(ssh, pids)
            users_by_pid = get_users_by_pid(ps_output)

            users = set((users_by_pid[pid] for pid in pids))
            real_users = [pwd.getpwnam(user).pw_gecos.split(',')[0] for user in users]

            info['users'] = users
            info['real_users'] = real_users

            update_users(info)

        gpu_infos.append(info)

    return gpu_infos


def get_remote_info(server):
    # returns gpu information from cache
    tstring = cache['servers'][server]['time'].strftime('%d.%m.%Y %H:%M:%S')
    logger.info(f'Using cache for {server} from {tstring}')

    return cache['servers'][server]['info']


def update_cache(interval):
    #  asyncronously updates cache if interval is passed
    logging.info('updating cache')
    for server in config.servers:
        try:
            logging.info(f'loading server {server}')
            config.ssh.connect(server, username=config.user, password=config.key)
            cache['servers'][server]['info'] = get_gpu_infos(config.ssh)
            cache['servers'][server]['time'] = datetime.now()
            config.ssh.close()
        except Exception:
            logging.error(f'Had an issue while updating cache for {server}: {traceback.format_exc()}')
    with open(config.cache_file, 'wb') as f:
        pickle.dump(cache, f)
    threading.Timer(interval.total_seconds(), update_cache, (interval, )).start()


def start_async(interval):
    # asyncronously updates cache
    threading.Thread(target=update_cache, args=(interval, )).start()


def setup():
    cache['servers'] = {server: {'time': datetime.fromtimestamp(0.), 'info': []} for server in config.servers}
    # start async updates of cache
    if os.path.isfile(config.cache_file):
        with open(config.cache_file, 'rb') as f:
            cache.update(pickle.load(f))
    start_async(config.update_interval)
