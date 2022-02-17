# import requests
# from datetime import datetime
# from pathlib import Path
# import os
# import subprocess
# import time

import os
import sys

import time

from bs4 import BeautifulSoup

import requests

link = 'https://www.polimi.it/docenti-e-staff/bandi-e-concorsi/assegnidiricerca/archivio/?tx_wfqbe_pi1%5Bshowpage%5D%5B112%5D={}'

for i in range(1, 25):
    print("------- PAGE {} --------".format(i))
    r = requests.get(link.format(i))

    soup = BeautifulSoup(r.text, "html.parser")

    for bando in soup.find_all("p"):
        text = bando.text
        if "DEIB" in text:
            print(bando.text.strip())

# print(r.text)

exit()
time.sleep(1)
print('ciaooooo', sys.argv[0], sys.argv)
os.execv(sys.executable, ['python'] + [sys.argv[0]])




bashCommand = 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/eramalli/opensmoke++suite-0.13.0/lib && '
bashCommand += ' cd /home/eramalli/Execution_1799 && '
bashCommand += ' /home/eramalli/.opensmoke/opensmoke++suite-0.15.0/bin/OpenSMOKEpp_BatchReactor.sh --input ./input.dic'

#
# IP_PORT = 'http://127.0.0.1:8080/'
#
# ABSOLUTE_BASE_PATH = '/home/eramalli/'
#
# USERNAMES = ['andrea.nobili']
#
# TIME_SLEEP = 30
#
# POLICY = 'LOCAL'
#
# MAX_ACTIVE_PROCESS = 2
#
#
# def main():
#
#     while True:
#
#         try:
#             date_time_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
#
#             crawling_request = requests.post(IP_PORT + 'OpenSmoke/API/getExecutions', json={'username_list': USERNAMES})
#
#             if crawling_request.status_code == 200:
#
#                 exec_list = crawling_request.json()
#
#                 print('\r{} - Waiting {} executions...'.format(date_time_str, len(exec_list)), end='')
#
#                 if len(exec_list) > 0:
#
#                     first = exec_list[0]
#
#                     start_request = requests.post(IP_PORT + 'OpenSmoke/API/startExecution',
#                                                   json={'execution_id': first})
#
#                     if start_request.status_code == 200:
#
#                         info = start_request.json()
#
#                         # Creo folder execution
#                         absolute_base_path = ABSOLUTE_BASE_PATH + 'Execution_{}'.format(first)
#                         Path(absolute_base_path).mkdir(parents=True, exist_ok=True)
#                         Path(os.path.join(absolute_base_path, './kinetics/')).mkdir(parents=True, exist_ok=True)
#                         Path(os.path.join(absolute_base_path, './profiles/')).mkdir(parents=True, exist_ok=True)
#                         Path(os.path.join(absolute_base_path, './results/')).mkdir(parents=True, exist_ok=True)
#
#                         solver = info.pop('solver')
#                         input_files = info.pop('input_files')
#                         output_files = info.pop('output_files')
#
#                         for file in input_files:
#                             with open(os.path.join(absolute_base_path, file), 'w+') as f:
#                                 f.write(input_files[file])
#
#                         bashCommand = 'python Job.py -e {} -p {} -s {} -f {}'.format(first, absolute_base_path, solver,
#                                                                                      ' '.join(output_files))
#
#                         # TODO che fare se faccio start ma non sono in grado di lanciare?
#                         # Magari annullare start_time ? con API
#
#                         if POLICY == 'LOCAL':
#                             process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
#                             output, error = process.communicate()
#                         else:
#                             pass
#                     else:
#                         print('\r{} - Error starting execution - {}'.format(date_time_str, start_request.text), end='')
#             else:
#                 print('\r{} - Error Retrieving jobs - {}'.format(date_time_str, crawling_request.text), end='')
#
#         except requests.exceptions.ConnectionError:
#             print('\r{} - ConnectionError'.format(date_time_str), end='')
#
#         finally:
#             time.sleep(TIME_SLEEP)
#
#
# if __name__ == "__main__":
#     print(end='')
#     main()
