import argparse
import os
import time
import subprocess
import requests
import platform
from utils import read_config


def execute(exec_id, path, solver, files):
    results = {'execution_id': exec_id, 'errors': '', 'files': {}, 'automatic': True}

    try:
        OS_SYSTEM = platform.system()

        if OS_SYSTEM == 'Darwin' or OS_SYSTEM == 'Linux':
            bashCommand = 'export LD_LIBRARY_PATH={}:$LD_LIBRARY_PATH && '.format(CONFIG['LD_LIBRARY_PATH'])
            bashCommand += ' cd {} && '.format(path)
            bashCommand += ' echo | {}/OpenSMOKEpp_{}.sh --input ./input.dic'.format(CONFIG['OS_PATH'], solver)
        elif OS_SYSTEM == 'Windows':
            bashCommand = ' cd {} && '.format(path)
            bashCommand += ' echo | {}\OpenSMOKEpp_{}.exe --input ./input.dic'.format(CONFIG['OS_PATH'], solver)
        else:
            print('ERROR!!!!')
            # TODO .....
            return

        process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()
        output = output.decode('ascii')

        if 'Fatal error' in output:
            output = output[output.find('Fatal error:'):]
            results['errors'] = output[12: output.find('\n')].strip()
        elif process.returncode != 0:
            results['errors'] = 'Fatal Error'
        else:
            tmp = {}
            for file in files:
                tmp[file] = open(os.path.join(path, 'results', '{}.out'.format(file))).read()

            results['files'] = tmp

    except Exception as e:
        results['errors'] += str(e)

    finally:
        sent = False
        attempt = 0
        sleep = 5

        response_error_msg = ''

        while not sent and attempt < CONFIG['MAX_ATTEMPT']:
            try:
                send = requests.post('{}OpenSmoke/API/collectFiles'.format(CONFIG['IP_PORT']), json=results, verify=CONFIG['VERIFY'])

                if send.status_code == 200:
                    sent = True
                else:
                    send.raise_for_status()

            except requests.exceptions.ConnectionError:
                time.sleep(sleep)
                sleep *= sleep
                attempt += 1
            except requests.exceptions.HTTPError as e:
                response_error_msg = str(e)
                break

        if not sent:
            with open('./backup_collect.csv', 'a+') as file:
                file.write('{};{};{};{};{}\n'.format(exec_id, path, ','.join(files), results['errors'], response_error_msg))


def main():
    parser = argparse.ArgumentParser(description='')

    parser.add_argument('-e', '--execution', dest='execution', type=int, required=True,
                        help='Execution ID')
    parser.add_argument('-p', '--path', dest='path', type=str, required=True,
                        help='Execution folder path')
    parser.add_argument('-s', '--solver', dest='solver', type=str, required=True,
                        help='OS Solver')
    parser.add_argument('-f', '--files', metavar='F', type=str, nargs='+', required=True,
                        help='an integer for the accumulator')

    args = parser.parse_args()

    exec_id = args.execution
    path = args.path
    solver = args.solver
    files = args.files

    execute(exec_id=exec_id, path=path, solver=solver, files=files)


def set_config():
    if not CONFIG['VERIFY']:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



if __name__ == "__main__":
    CONFIG = read_config()
    set_config()

    main()
