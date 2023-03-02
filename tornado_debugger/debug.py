import os.path
import re
import sys
import traceback
from pprint import pformat
import tornado

from tornado import template
from tornado.escape import xhtml_escape


SENSITIVE_SETTINGS_RE = re.compile(
    'api|key|pass|salt|secret|signature|token',
    flags=re.IGNORECASE
)


def debugger_escape(value):
    """A custom escape function to handle UnicodeDecodeError.

    Sometimes some local variables in a function may have certain byte data
    which can't be decoded to string (such as xsrf tokens).

    Since we display all the local variables found in the traceback frames
    on the debugger page, all variables go through Tornado's ``xhtml_escape``
    function. The variables which can't be decode will raise UnicodeDecodeError.

    Hence, we create a custom function to deal with that.
    """
    try:
        return xhtml_escape(value)
    except UnicodeDecodeError:
        return value


class ExceptionReporter:
    def __init__(self, exc_info, handler):
        self.exc_type = exc_info[0]
        self.exc_value = exc_info[1]
        self.exc_tb = exc_info[2]
        self.handler = handler

    def get_response(self):
        loader = template.Loader(os.path.dirname(os.path.abspath(__file__)))
        t = loader.load('debug.html')
        return t.generate(
            traceback=traceback,
            pprint=pprint,
            handler=self.handler,
            app_settings=self.get_app_settings(),
            exc_type=self.exc_type,
            exc_value=self.exc_value,
            exc_tb=self.exc_tb,
            frames=self.get_traceback_frames(),
            tornado_version=tornado.version,
            sys_version='%d.%d.%d' % sys.version_info[0:3],
            sys_executable=sys.executable,
            sys_path=sys.path,
            debugger_escape=debugger_escape,
        )

    def get_app_settings(self):
        settings = {}

        for arg, value in self.handler.application.settings.items():
            if SENSITIVE_SETTINGS_RE.search(arg):
                value = '*' * 15
            settings[arg] = value

        return settings

    def get_source_lines(self, tb):
        filename = tb.tb_frame.f_code.co_filename
        lineno = tb.tb_lineno
        lines = []
        try:
            with open(filename, 'rb') as f:
                _lines = f.read().splitlines()
                for _lineno in range(
                    max(lineno - 5, 0), 
                    min(lineno + 5, len(_lines))
                ):
                    lines.append((_lineno + 1, _lines[_lineno]))
        except Exception as e:
            # could not open file
            pass

        return lines

    def get_traceback_frames(self):
        frames = []

        tb = self.exc_tb
        while tb:
            frames.append({
                'lineno': tb.tb_lineno,
                'filename': tb.tb_frame.f_code.co_filename,
                'function': tb.tb_frame.f_code.co_name,
                'module_name': tb.tb_frame.f_globals.get('__name__') or '',
                'vars': tb.tb_frame.f_locals,
                'lines': self.get_source_lines(tb),
            })
            tb = tb.tb_next

        frames.reverse()
        return frames 

        exceptions = []
        exc_value = self.exc_value
        while exc_value:
            exceptions.append(exc_value)
            exc_value = self._get_explicit_or_implicit_cause(exc_value)
            if exc_value in exceptions:
                warnings.warn(
                    "Cycle in the exception chain detected: exception '%s' "
                    "encountered again." % exc_value,
                    ExceptionCycleWarning,
                )
                # Avoid infinite loop if there's a cyclic reference (#29393).
                break

        frames = []
        # No exceptions were supplied to ExceptionReporter
        if not exceptions:
            return frames

        # In case there's just one exception, take the traceback from self.tb
        exc_value = exceptions.pop()
        tb = self.tb if not exceptions else exc_value.__traceback__
        while True:
            frames.extend(self.get_exception_traceback_frames(exc_value, tb))
            try:
                exc_value = exceptions.pop()
            except IndexError:
                break
            tb = exc_value.__traceback__
        return frames

    def _get_explicit_or_implicit_cause(self, exc_value):
        explicit = getattr(exc_value, '__cause__', None)
        suppress_context = getattr(exc_value, '__suppress_context__', None)
        implicit = getattr(exc_value, '__context__', None)
        return explicit or (None if suppress_context else implicit)


def pprint(value):
    try:
        return pformat(value, width=1)
    except Exception as e:
        return 'Error in formatting: %s: %s' % (e.__class__.__name__, e)
