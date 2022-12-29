import os
from SciExpeM import settings
import tempfile
import subprocess
import time
from ExperimentManager.Models import ChemModel


class ReSpecThConverter:
    path = settings.RESPECTH_CONVERTER_PATH

    base_input = '''
    
    Dictionary RespecthConverter
    {
        @KineticsFolder            ZZ;
        @KineticsFolderRemote      $PATHKINETICFOLDER$;
        @InputFolder               XX;
        @OutputFolderRemote        YY;
        @CaseSensitiveSpecies      false;
    }
    
    '''

    @staticmethod
    def convert(respecth_txt):
        # create a temporary directory
        with tempfile.TemporaryDirectory() as sandbox:
            tmp_txt_file_name = "tmp.xml"
            tmp_txt_file_name_path = os.path.join(sandbox, tmp_txt_file_name)
            tmp_txt_file = open(tmp_txt_file_name_path, "w+")
            tmp_txt_file.write(respecth_txt)
            tmp_txt_file.close()

            input_dic_file_name_path = os.path.join(sandbox, 'input.dic')
            input_dic_file = open(input_dic_file_name_path, "w+")
            input_dic_text_file = ReSpecThConverter.base_input.replace('XX', sandbox).replace('YY', sandbox).replace('ZZ', ChemModel.objects.get(id=24).absolute_folder_xml_file_kinetics_path)
            input_dic_file.write(input_dic_text_file)
            input_dic_file.close()

            # print(sandbox)

            bashCommand = "cd " + ReSpecThConverter.path + " && "
            bashCommand += "echo |  ./ReSpecThConverter "
            bashCommand += tmp_txt_file_name_path
            bashCommand += " --input "
            bashCommand += os.path.join(sandbox, 'input.dic')

            # print(bashCommand)

            # time.sleep(1000)

            process = subprocess.Popen(bashCommand,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            output = output.decode('ascii')

            error_text = ''

            if 'Fatal error' in output:
                output = output[output.find('Fatal error:'):]
                error_text = output[12: output.find('\n')].strip()
            elif process.returncode != 0:
                if error:
                    error_text = error.decode('ascii')
                else:
                    error_text = 'Fatal Error'

            if error_text:
                return None, error_text
            else:
                result_path = os.path.join(sandbox, 'tmp.xml.dic')
                with open(result_path, 'r') as file:
                    return file.read(), error_text

# def convertReSpecTh(respecth_txt):
