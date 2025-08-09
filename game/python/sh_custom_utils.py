# ---------------------------------------------------------------------------
#           Name: sh_custom_utils.py
#    Description: additional utils
# ---------------------------------------------------------------------------


import sys
import traceback
import re
import datetime
import sh_io

last_exception = {'file': '', 'line': '', 'traceback_msg': ''}


class ExceptionData:
    # Example: a = 1 / 0
    def __init__(self):
        self.exception = {'file': '', 'line': '', 'traceback_msg': ''}
        try:
            # exception_type:       <class 'ZeroDivisionError'>
            # exception_value:      division by zero
            # exception_traceback:  <traceback object at 0x7f5ff5c55088>
            exception_type, exception_value, exception_traceback = sys.exc_info()

            # [
            #   'Traceback (most recent call last):',
            #   '  File "/../../python/sh_custom_utils.py", line 95, in <module>',
            #   '    a = 1 / 0',
            #   'ZeroDivisionError: division by zero'
            # ]
            exception_info = traceback.format_exc().splitlines()

            # [
            # split:
            #   '  File "/../../python/sh_custom_utils.py"',
            #   ' line 109',
            #   ' in <module>',
            # append:
            #   '    a = 1 / 0'
            # ]
            root_info = []
            if len(exception_info) > 1:
                root_info = str(exception_info[1]).split(",")
            if len(exception_info) > 2:
                root_info.append(exception_info[2])

            # [
            #   'File "/../../python/sh_custom_utils.py"',
            #   'line 109',
            #   'in <module>',
            #   'a = 1 / 0'
            # ]
            for index in range(0, 4):
                if len(root_info) < index:
                    root_info.append("<empty>")
                else:
                    root_info[index] = root_info[index].strip()

            # ['sh_custom_utils.py', 'line 130', 'in <module>', 'a = 1 / 0']
            root_info[0] = root_info[0].split("/")[-1].replace("\"", "")

            # file: [sh_custom_utils.py], method: test()
            top_file_name = str(exception_traceback.tb_frame.f_code.co_filename).split("/")[-1]
            top_method_name = str(exception_traceback.tb_frame.f_code.co_name)
            del (exception_type, exception_value, exception_traceback)

            # 2019.10.10 - 22:45:21
            exception_timestamp = datetime.datetime.now().strftime("%Y.%m.%d - %H:%M:%S")

            # 2019.10.10 - 22:45:21:
            #   Top:  file: [sh_custom_utils.py], method: test()
            #   Root: file: [sh_custom_utils.py], line 110, cause: in test [a = 1 / 0]
            #   ZeroDivisionError: division by zero
            traceback_msg = '\n%s:\n' % exception_timestamp
            traceback_msg += "  Top:  file: [%s], method: %s()\n" % (top_file_name, top_method_name)
            traceback_msg += "  Root: file: [%s], %s, cause: %s [%s]\n" % \
                             (root_info[0], root_info[1], root_info[2], root_info[3])
            traceback_msg += "  " + exception_info[-1] + "\n"

            self.exception['file'] = root_info[0]
            self.exception['line'] = root_info[1]
            self.exception['traceback_msg'] = traceback_msg

        except:
            self.exception['traceback_msg'] = "\nError in resolving exception\n" + traceback.format_exc() + "\n"

    def get_exception(self):
        return self.exception

    def __str__(self):
        return self.exception['traceback_msg']


def get_and_log_exception_info():
    exception = ExceptionData().get_exception()

    global last_exception
    # Escape logging of the same exceptions that can happen inside the loops
    if not (last_exception["file"] == exception['file'] and last_exception["line"] == exception['line']):
        last_exception['traceback_msg'] = exception['traceback_msg']
        last_exception["file"] = exception['file']
        last_exception["line"] = exception['line']

        sh_io.save_to_file("exceptions", last_exception['traceback_msg'])


def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text


def obj_repr(obj):
    if hasattr(obj, 'json_repr'):
        return obj.json_repr()
    else:
        return obj.__dict__


def clear_clans_and_colors(body):
    replacement = ""
    body = re.sub("\^clan [0-9]{0,10}\^", replacement, body)
    body = re.sub("\^[a-z|A-Z]", replacement, body)
    body = re.sub("\^[0-9]{3}", replacement, body)
    body = body.strip()
    return body


def time_formatter(seconds):
    minutes = int(seconds / 60)
    seconds = int(seconds % 60)
    return "%s:%s" % (minutes, seconds)
