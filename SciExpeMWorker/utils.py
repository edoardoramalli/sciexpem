import os
import json
import psutil
import glob
import warnings

def read_config():
    config_file_path = './sciexpem.config'
    MANDATORY = [
        'ABSOLUTE_BASE_PATH',
        'IP_PORT',
        'MAX_ACTIVE_JOBS',
        'POLICY',
        'TIME_SLEEP',
        'USERNAMES',
        'VERIFY',
        'LD_LIBRARY_PATH',
        'OS_PATH',
        'MAX_ATTEMPT',
        'BACKUP_PATH_FILE']
    if os.path.isfile(config_file_path):
        with open(config_file_path, 'r') as file:
            config = json.load(file)
            if set(MANDATORY) != set(config.keys()):
                raise ValueError('Missing settings: {}'.format(set(MANDATORY) - set(config.keys())))
            return config
    else:
        raise ValueError('Impossible to read config file')


def generate_PBS(file_path, command):
    template_pbs_file_path = './template_pbs.pbs'
    with open(template_pbs_file_path, 'r') as file_read:
        string_pbs = file_read.read()
        string_pbs = string_pbs.replace('__COMMAND', command)

    with open(file_path, 'w+') as file_write:
        file_write.write(string_pbs)


def check_available_cpu_cores(threshold=15):
    # TODO volendo si può complicare e controllare il tempo in idle usando cpu_times_percent comed double check
    status_cores = psutil.cpu_percent(interval=1, percpu=True)
    num_available = sum([1 if p_core <= threshold else 0 for p_core in status_cores])
    return num_available


def check_config(CONFIG, NUM_CORES=None):
    # Check if LD_LIBRARY_PATH and OS_PATH exists
    if not os.path.isdir(CONFIG['LD_LIBRARY_PATH']):
        raise ValueError('{} directory does not exist'.format(CONFIG['LD_LIBRARY_PATH']))

    if not os.path.isdir(CONFIG['OS_PATH']):
        raise ValueError('{} directory does not exist'.format(CONFIG['OS_PATH']))

    if not os.path.isdir(CONFIG['ABSOLUTE_BASE_PATH']):
        raise ValueError('{} directory does not exist'.format(CONFIG['ABSOLUTE_BASE_PATH']))

    list_executables_os = glob.glob(os.path.join(CONFIG['OS_PATH'], '*.sh'))
    list_executables_lib = glob.glob(os.path.join(CONFIG['LD_LIBRARY_PATH'], '*.so')) + glob.glob(
        os.path.join(CONFIG['LD_LIBRARY_PATH'], '*.so.*'))

    for executable in list_executables_os + list_executables_lib:
        if not os.access(path=executable, mode=os.X_OK):
            raise ValueError('{} no permission to execute'.format(executable))

    if not os.access(path=CONFIG['ABSOLUTE_BASE_PATH'], mode=os.W_OK):
        raise ValueError('{} no permission to write'.format(CONFIG['ABSOLUTE_BASE_PATH']))

    if not os.access(path=CONFIG['ABSOLUTE_BASE_PATH'], mode=os.R_OK):
        raise ValueError('{} no permission to read'.format(CONFIG['ABSOLUTE_BASE_PATH']))

    if NUM_CORES:
        if not 0 <= CONFIG['MAX_ACTIVE_JOBS'] <= NUM_CORES:
            raise ValueError('Config MAX_ACTIVE_JOBS={} not valid. Should be between 0 and # of cores'.format(
                CONFIG['MAX_ACTIVE_JOBS']))

        if CONFIG['MAX_ACTIVE_JOBS'] == NUM_CORES:
            warnings.warn('Dangerous configuration MAX_ACTIVE_JOBS==NUM_OF_CORES')