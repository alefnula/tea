v0.0.4 (August XX, 2013)
------------------------

  - Added list to ``config`` commander command, and fixed add to create a list
    if it doesn't exist.
  - Added a hack for positional arguments in commands.
  - Adding safe and unsafe methods to the Config and MultiConfig classes. Safe
    methods will never raise and error. They will either swallow the exception
    or return a default value. Unsafe methods will raise either KeyError or
    IndexError. (removed ConfigError)
  - Removed the ``execute_free*`` functions. Nobody uses them, and actually
    they are just confusing. 


v0.0.3 (July 27, 2013)
----------------------

  - Added ``ds.config.Config`` and ``ds.config.MultiConfig`` data structures
  - Change the ``configure_logging`` method to be more pythonic
  - Add API documentation
