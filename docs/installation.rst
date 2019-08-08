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

    $ pip install iniesta[development] # in bash
    $ pip install 'iniesta[development]' # in zsh
    # installs test packages + sphinx + sphinx_rtd_theme

    $ pip install iniesta[release] # in bash
    $ pip install 'iniesta[release]' # in zsh
    # install necessary packages for releasing (eg. zest.releaser)

    $ pip install iniesta[cli] # in bash
    $ pip install 'iniesta[cli]' # in zsh
    # install packages for cli
