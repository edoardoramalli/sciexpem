import argparse
import os
import sys
import subprocess
import requests


def execute(exec_id, path, solver, files):
    results = {'execution_id': exec_id, 'errors': '', 'files': {}}

    try:
        bashCommand = 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/eramalli/opensmoke++suite-0.13.0/lib && '
        bashCommand += ' cd {} && '.format(path)
        bashCommand += ' /home/eramalli/.opensmoke/opensmoke++suite-0.15.0/bin/OpenSMOKEpp_' + solver + ".sh --input ./input.dic"

        process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()
        output = output.decode('ascii')

        if 'Fatal error' in output:
            output = output[output.find('Fatal error:'):]
            results['error'] = output[12: output.find('\n')].strip()
        else:
            tmp = {}
            for file in files:
                tmp[file] = open(os.path.join(path, 'results', '{}.out'.format(file))).read()

            results['files'] = tmp

    except Exception as e:
        results['error'] += str(e)

    finally:
        print(results)
        send = requests.post('http://127.0.0.1:8080/OpenSmoke/API/collectFiles', json=results)
        print(send.text)
        # Che fare se c'è errore?


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


if __name__ == "__main__":
    main()
