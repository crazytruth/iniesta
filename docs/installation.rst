============
Installation
============

At the command line either via easy_install or pip::

    $ easy_install iniesta
    $ pip install iniesta

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv iniesta
    $ pip install iniesta

Iniesta also includes various extras::

    $ pip install iniesta[development]
    # installs test packages + sphinx + sphinx_rtd_theme

    $ pip install iniesta[release]
    # install necessary packages for releasing (eg. zest.releaser)

    $ pip install iniesta[cli]
    # install packages for cli in bash shell
    $ pip install 'iniesta[cli]'
    # install packages for cli in zsh shell
