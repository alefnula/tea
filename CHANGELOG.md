# CHANGELOG

## v0.1.2 (August 24, 2020)

- Added TeaError as a base class for all submodule errors.


---


## v0.1.1 (August 23, 2020)

- Make singleton initialization thread safe.


---


## v0.1.0 (August 23, 2020)

- Module cleanup. Remove all unused modules.
- Remove support for python2 and IronPython.
- Remove unnecessary windows specific modules.
- License change from BSD to Apache-2.0.
- Added timestamp module.
- Process module enhanced.
- Fixes for python3.


---


## v0.0.6 (February XX, 2014)

- Change project organization.
- Remove tornado JsonHandler. It is too application specific to be in a
  common library such as tea.
- `environment` parameter in the `process` module changed to `env`.
  Creation of full environment moved to the base `Process` class.
- Adding `working_dir` parameter to the `Process` class constructor.
- Rename tea.shutil to tea.shell
- Added `tea.shell.gremove`
- Added `ctx` - context manager library
- Added `tea.utils.load_subclasses`
- Remove the `tea.cron` module. The same thing can be found in the
  `APScheduler` python package on PyPI.
- Add `tea.shell.touch` and hide helper functions in `tea.shell`.


---


## v0.0.5 (October 12, 2013)


- Porting everything to work with Python 2.7 and Python 3.3.
- Adding `six` library to `utils` module.
- Adding `docstring` decorator.
- Refactoring the `process` module. Removing duplicate functions and merging
  all `execute_` functions to a single `execute`.


---


## v0.0.4 (August 04, 2013)

- Fix in the `tea.process.posix_process` when killing a process.
- Adding tests for the `tea.process` module.
- Process.is_running is now a property instead of a method 
- Added abstract base class for the Process in the `tea.process` module,
  now every platform specific implementation will conform to the interface of
  the Process class
- Added list to `config` commander command, and fixed add to create a list
  if it doesn't exist.
- Added a hack for positional arguments in commands.
- Adding safe and unsafe methods to the Config and MultiConfig classes. Safe
  methods will never raise and error. They will either swallow the exception
  or return a default value. Unsafe methods will raise either KeyError or
  IndexError. (removed ConfigError)
- Removed the `execute_free*` functions. Nobody uses them, and actually
  they are just confusing. 


---


## v0.0.3 (July 27, 2013)

- Added `ds.config.Config` and `ds.config.MultiConfig` data structures.
- Change the `configure_logging` method to be more pythonic.
- Add API documentation.
