# tornado-debugger

A debugger for Tornado server for a better development experience.

Tornado's default exception reporter is very basic and primitive. `tornado-debugger` is
a drop-in replacement for the built-in debugger.


## Install

```sh
$ pip install tornado-debugger
```


## Usage

Use the `DebuggerMixin` class to automatically add the debugger features.
This mixin class overrides `RequestHandler.write_error` method and will display
a detailed error page.

```python
from tornado import web
from tornado_debugger import DebuggerMixin


class IndexHandler(DebuggerMixin, web.RequestHandler):
    # always inherit from mixin class BEFORE the base class

    def get(self):
        1/0
```

**Note:** The `DebuggerMixin` only works in debug mode (i.e. when `debug=True` in the Application settings).


## Screenshot

![tornado-debugger screenshot](https://raw.githubusercontent.com/bhch/tornado-debugger/master/screenshot.png)


## License

[BSD-3-Clause](LICENSE.txt)
