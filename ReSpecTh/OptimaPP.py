import tempfile
import subprocess
import os
import sys


class OptimaPP:

    @staticmethod
    def txt_to_xml(txt):

        # create a temporary directory
        with tempfile.TemporaryDirectory() as sandbox:
            tmp_txt_file_name = "tmp.txt"
            tmp_txt_file_name_path = os.path.join(sandbox, tmp_txt_file_name)
            tmp_txt_file = open(tmp_txt_file_name_path, "w+")
            tmp_txt_file.write(txt)
            tmp_txt_file.close()

            bashCommand = "cd /home/eramalli/source_code/build/bin/Release && "
            bashCommand += " ./OptimaPP TXT_TO_XML "
            bashCommand += tmp_txt_file_name_path
            bashCommand += " -o "
            bashCommand += sandbox

            process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
            output, error = process.communicate()
            output = str(output)
            # print(output, file=sys.stderr)

            txt_start_warning = "-------------------------------------- + ---------------------------------------"

            if error is None:
                error = ""

            error += output[output.find(txt_start_warning) + len(txt_start_warning) + 2: output.rfind("Completed")]

            # print("EDOOOO\n",file=sys.stderr)
            # print(error, file=sys.stderr)

            if not error:
                xml_result_path = os.path.join(sandbox, "tmp.xml")
                xml_file_string = open(xml_result_path, "r").readlines()
                return xml_file_string, None
            else:
                return None, error
