==============
Configurations
==============

A couple of configurations.

AWS Sessions
============

You can currently set 3 aws configurations that iniesta will take.

- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION

You can override the default by prefixing `INIESTA_` to the aws
environment variable name in vault to override.

Example:

.. code-block:: python

    INIESTA_AWS_ACCESS_KEY_ID
    INIESTA_AWS_SECRET_ACCESS_KEY
    INIESTA_AWS_DEFAULT_REGION

Priority
--------

1. `INIESTA_*` prefixed variables in insanic settings.
2. `AWS_*` variables in insanic settings.
3. `AWS_*` variables in environment variables.


The loaded variables can be accessed in `BotoSession.*` where * is the
aws environment variable name in lowercase.
