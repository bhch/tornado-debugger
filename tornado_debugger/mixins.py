from tornado_debugger.debug import ExceptionReporter


class DebuggerMixin:
    def write_error(self, status_code, **kwargs):
        """Override RequestHandler's write_error method to render
        a custom error page.
        """
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            reporter = ExceptionReporter(kwargs["exc_info"], self)
            self.write(reporter.get_response())
            self.finish()
        else:
            super().write_error(status_code, **kwargs)
