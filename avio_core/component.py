from random import randint
from circuits import Component
from avio_core.logger import hfoslog
import inspect
import traceback
from sys import exc_info

class AVIOComponent(Component):
    debug = False

    names = []

    def __init__(self, uniquename=None, *args, **kwargs):
        super(AVIOComponent, self).__init__(*args, **kwargs)

        if not uniquename:
            uniquename = self.name

        if uniquename in self.names:
            new_uniquename = uniquename
            while new_uniquename in self.names:
                new_uniquename = uniquename + str(randint(2**16))
            uniquename = new_uniquename

        self.uniquename = uniquename


    def log(self, *args, **kwargs):
        """Log a statement from this component"""

        func = inspect.currentframe().f_back.f_code
        # Dump the message + the name of this function to the log.

        if 'exc' in kwargs and kwargs['exc'] is True:
            exc_type, exc_obj, exc_tb = exc_info()
            line_no = exc_tb.tb_lineno
            # print('EXCEPTION DATA:', line_no, exc_type, exc_obj, exc_tb)
            args += traceback.extract_tb(exc_tb),
        else:
            line_no = func.co_firstlineno

        sourceloc = "[%.10s@%s:%i]" % (
            func.co_name,
            func.co_filename,
            line_no
        )
        hfoslog(sourceloc=sourceloc, emitter=self.uniquename, *args, **kwargs)

