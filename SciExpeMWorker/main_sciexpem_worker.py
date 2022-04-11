import psutil
import requests
from datetime import datetime
from pathlib import Path
import subprocess
import time
import sys
import requests
import hashlib
import os
import threading
import argparse
import utils_sciexpem_worker as utils
import platform
import random

VERSION = '0.0.0.1'


def increase_active_jobs():
    global ACTIVE_JOBS
    LOCK_ACTIVE_JOBS.acquire()
    ACTIVE_JOBS += 1
    LOCK_ACTIVE_JOBS.release()


def decrease_active_jobs():
    global ACTIVE_JOBS
    LOCK_ACTIVE_JOBS.acquire()
    ACTIVE_JOBS -= 1
    LOCK_ACTIVE_JOBS.release()


def try_to_start_job():
    global ACTIVE_JOBS
    LOCK_ACTIVE_JOBS.acquire()
    if ACTIVE_JOBS < CONFIG['MAX_ACTIVE_JOBS']:
        ACTIVE_JOBS += 1
        success = True
    else:
        success = False
    LOCK_ACTIVE_JOBS.release()
    return success


def start_job(execution_id):
    try:
        start_request = requests.post(CONFIG['IP_PORT'] + 'OpenSmoke/API/startExecution',
                                      json={'execution_id': execution_id, 'computer': COMPUTER_NAME},
                                      verify=CONFIG['VERIFY'])

        if start_request.status_code == 200:

            info = start_request.json()

            # Creo folder execution
            absolute_base_path = os.path.join(CONFIG['ABSOLUTE_BASE_PATH'], 'Execution_{}'.format(execution_id))
            Path(absolute_base_path).mkdir(parents=True, exist_ok=True)
            Path(os.path.join(absolute_base_path, './kinetics/')).mkdir(parents=True, exist_ok=True)
            Path(os.path.join(absolute_base_path, './profiles/')).mkdir(parents=True, exist_ok=True)
            Path(os.path.join(absolute_base_path, './results/')).mkdir(parents=True, exist_ok=True)

            solver = info.pop('solver')
            input_files = info.pop('input_files')
            output_files = info.pop('output_files')

            for file in input_files:
                with open(os.path.join(absolute_base_path, file), 'w+') as f:
                    f.write(input_files[file])

            bashCommand = 'python job_sciexpem_worker.py -e {} -p {} -s {} -f {}'.format(execution_id, absolute_base_path, solver,
                                                                         ' '.join(output_files))

            # TODO che fare se faccio start ma non sono in grado di lanciare?
            # Magari annullare start_time ? con API

            if CONFIG['POLICY'] == 'LOCAL':
                process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
                output, error = process.communicate()
                decrease_active_jobs()
            elif CONFIG['POLICY'] == 'PBS':
                pbs_file_path = os.path.join(absolute_base_path, 'Execution_{}.pbs'.format(execution_id))
                utils.generate_PBS(file_path=pbs_file_path, command=bashCommand)

                process = subprocess.Popen('qsub -Wblock=true {}'.format(pbs_file_path),
                                           shell=True,
                                           stdout=subprocess.PIPE)
                output, error = process.communicate()
                decrease_active_jobs()
            else:
                decrease_active_jobs()
                pass

        elif start_request.status_code == 400:
            print('\nError concurrency starting execution {}'.format(execution_id))
            print(end='')
            # decrease_active_jobs()

    except Exception as e:
        results = {'execution_id': execution_id, 'errors': str(e), 'files': {}, 'automatic': True}
        send = requests.post('{}OpenSmoke/API/collectFiles'.format(CONFIG['IP_PORT']), json=results,
                             verify=CONFIG['VERIFY'])
        # TODO che fare se non riesco ad inviare?

        decrease_active_jobs()
        print('\nError starting execution - {}'.format(str(e)))
        print(end='')


def crawling_jobs():
    try:
        crawling_request = requests.post(CONFIG['IP_PORT'] + 'OpenSmoke/API/getExecutions',
                                         json={'username_list': CONFIG['USERNAMES'],
                                               'computer': COMPUTER_NAME,
                                               'free_cores': NUM_FREE_CORES,
                                               'num_cores': NUM_CORES,
                                               'max_jobs': CONFIG['MAX_ACTIVE_JOBS'],
                                               'active_jobs': ACTIVE_JOBS},
                                         verify=CONFIG['VERIFY'])

        if crawling_request.status_code == 200:
            return crawling_request.json()
        else:
            return []

    except requests.exceptions.ConnectionError:
        print('\nCrawling Jobs - ConnectionError')
        print(end='')
        return []


def start_job_test(num):
    import random
    time.sleep(random.randint(5, 10))
    decrease_active_jobs()


def crawling_jobs_test():
    import random
    return [random.randint(0, 50) for _ in range(random.randint(0, 5))]


def main():
    global WAITING
    global NUM_FREE_CORES

    if CONFIG['POLICY'] == 'LOCAL':
        NUM_FREE_CORES = utils.check_available_cpu_cores()
        if NUM_FREE_CORES <= 0:
            WAITING = 'Undefined'
            return

    exec_list = crawling_jobs()
    WAITING = len(exec_list)

    if len(exec_list) > 0:
        # TODO pensare se qui fare una versione hungry: cerco di svuotare la lista se possibile finchè ho spazio
        # In questo caso però bisogna ogni volta controllare i core liberi
        first = exec_list[0]
        if try_to_start_job():
            threading.Thread(target=start_job, args=(first,), daemon=CONFIG['POLICY'] == 'LOCAL').start()


def upload():
    current = None
    remainder = ''
    with open(os.path.join(CONFIG['ABSOLUTE_BASE_PATH'], 'backup_collect.csv'), 'r') as reader:
        current = reader.readline()
        for line in reader:
            remainder += line
        reader.close()

    if current:

        current_split = current.split(';')

        execution_id = current_split[0]
        path = current_split[1]
        files = current_split[2]
        errors = current_split[3]

        tmp = {}
        for file in files:
            tmp[file] = open(os.path.join(path, 'results', '{}.out'.format(file))).read()

        results = {'execution_id': execution_id, 'errors': errors, 'files': tmp}

        send = requests.post('{}OpenSmoke/API/collectFiles'.format(CONFIG['IP_PORT']),
                             json=results, verify=CONFIG['VERIFY'])

        if send.status_code != 200:
            remainder += current

    if remainder:
        with open('./backup_collect.csv', 'w') as writer:
            writer.writelines(remainder)
            writer.close()


def set_config():
    if not CONFIG['VERIFY']:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def checkUpdate():
    cwd = os.getcwd()
    h = hashlib.md5()

    r = requests.post(CONFIG['IP_PORT'] + 'OpenSmoke/API/checkUpdate', verify=CONFIG['VERIFY'])

    if r.status_code != 200:
        return

    files = r.json()

    for file in files:
        with open(os.path.join(cwd, file), 'r', encoding='utf-8') as f:
            text = f.read()
            h.update(text.encode('utf-8'))
            if files[file] != h.hexdigest():
                r = requests.post(CONFIG['IP_PORT'] + 'OpenSmoke/API/getUpdate', verify=CONFIG['VERIFY'])
                update_files = r.json()

                for new_files in update_files:
                    with open(os.path.join(cwd, new_files), 'w', encoding='utf-8') as f_write:
                        f_write.write(update_files[new_files])

                # os.execv(sys.executable, ['python'] + [sys.argv[0]] + ['-a {}'.format(ACTIVE_JOBS)])
                os.execv(sys.executable, ['python'] + [sys.argv[0]])


def print_status():
    # TODO pensare se e come fare il display dell'esecuzione della macchina
    # Facendo attenzione al riavvio in caso di update
    date_time_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    msg = ' {} ---> '.format(date_time_str)
    msg += 'Jobs {}/{} - '.format(ACTIVE_JOBS, CONFIG['MAX_ACTIVE_JOBS'])
    msg += 'Waiting {} - '.format(WAITING)
    if CONFIG['POLICY'] == 'LOCAL':
        msg += 'Free Cores {}/{} - '.format(NUM_FREE_CORES, NUM_CORES)
    msg += ''
    print('\r {}'.format(msg), end='')


if __name__ == "__main__":
    global ACTIVE_JOBS
    global WAITING
    global NUM_FREE_CORES
    global NUM_CORES
    global COMPUTER_NAME

    WAITING = 0
    NUM_FREE_CORES = -1
    NUM_CORES = psutil.cpu_count()
    COMPUTER_NAME = platform.node()

    # parser = argparse.ArgumentParser(description='')
    # parser.add_argument('-a', '--active', dest='active', type=int, required=False, help='Do not use it!')
    # args = parser.parse_args()
    # ACTIVE_JOBS = args.active if args.active else 0

    ACTIVE_JOBS = utils.find_zombie_jobs()

    CONFIG = utils.read_config()
    utils.check_config(CONFIG=CONFIG, NUM_CORES=NUM_CORES if CONFIG['POLICY'] == 'LOCAL' else None)
    set_config()
    LOCK_ACTIVE_JOBS = threading.Lock()

    print()
    print('--> Version {}'.format(VERSION))
    print('--> Configuration of {}:'.format(COMPUTER_NAME))
    for conf in CONFIG:
        print('\t', conf, '=', CONFIG[conf])
    print(end='')

    SLEEP_TIME = CONFIG['TIME_SLEEP'] + random.randint(0, int(CONFIG['TIME_SLEEP'] * 20 / 100))

    while True:
        checkUpdate()

        print_status()

        if CONFIG['POLICY'] == 'LOCAL':
            ACTIVE_JOBS = utils.find_zombie_jobs()

        if ACTIVE_JOBS < CONFIG['MAX_ACTIVE_JOBS']:
            main()
        else:
            WAITING = '~'
        time.sleep(SLEEP_TIME)
