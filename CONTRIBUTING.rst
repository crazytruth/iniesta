..

Contributing to Iniesta
========================

Thank you for considering to contribute to Iniesta.

Requirements for development
-----------------------------

Requirements for AWS

- Environment Variable Settings for AWS
    You need to add this environment variable file in ``~/.aws/`` directory with following file name.

    In file name ``config``:

    .. code-block:: vim

        [default]
        region = us-east-1
    ..

    In file name ``credentials``:

    .. code-block:: vim

        [default]
        aws_access_key_id = YOUR_ACCESS_KEY_ID
        aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
    ..

    **For Credentials, You have better set it as Environment Variable in your IDE.**

    You can refer to AWS credentials for AWS CLI document_.

    .. _document : https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html


-  AWS Policy Settings
    You need to add policies related to actions of SQS and SNS.
    The following actions need to be added in your IAM.

    SQS:

    .. code-block:: bash

        "Action": [
                "sqs:DeleteMessage",
                "sqs:GetQueueUrl",
                "sqs:DeleteMessageBatch",
                "sqs:ReceiveMessage",
                "sqs:DeleteQueue",
                "sqs:SendMessage",
                "sqs:GetQueueAttributes",
                "sqs:CreateQueue",
                "sqs:SetQueueAttributes"
            ],
        "Resource": "arn:aws:sqs:ap-northeast-1:<aws_account_id>:iniesta-test-*"
    ..

    SNS:

    .. code-block:: text

        "Action": [
                    "sns:ListSubscriptionsByTopic",
                    "sns:Publish",
                    "sns:GetTopicAttributes",
                    "sns:DeleteTopic",
                    "sns:CreateTopic",
                    "sns:Subscribe",
                    "sns:Unsubscribe",
                    "sns:GetSubscriptionAttributes"
                ],
        "Resource": "arn:aws:sns:ap-northeast-1:<aws_account_id>:test-test-global-*"


OR we can use localstack.

Install localstack

.. code-block:: text

    $ pip install localstack
    $ SERVICES=sns,sqs localstack start

You will need to change the Endpoint urls for SNS and SQS.


Setup for development
-----------------------

-   Fork Iniesta to your GitHub account.
-   `Clone`_ the Iniesta repository locally.

    .. code-block:: text

        $ git clone https://github.com/crazytruth/iniesta
        $ cd iniesta

-   Add your fork as a remote to push your work to. Replace
    ``{username}`` with your username. This names the remote "fork", the
    default crazytruth remote is "origin".

    .. code-block:: text

        git remote add fork https://github.com/{username}/iniesta

-   Create a virtualenv with `pyenv`_ and `pyenv-virtualenv`_.

    -   Prerequisites for creating a virtualenv

        Please install `pyenv`_ and `pyenv-virtualenv`_ if you dont have them
        installed.

        You must also install the Python versions with :code:`pyenv`.

        .. code-block:: bash

            # to view available python versions
            $ pyenv install --list

            # to install python 3.6.12
            $ pyenv install 3.6.12

    Now to settings the virtual environment.

    Replace ``{pythonversion}`` with the python version to
    create the virtual environment in.

    .. code-block:: bash

        $ pyenv virtualenv {pythonversion} iniesta
        $ pyenv local iniesta

-   Install Iniesta in editable mode with development dependencies.

    .. code-block:: text

        $ pip install -e . -r requirements/dev.txt

-   Install the pre-commit hooks.

    .. code-block:: text

        $ pre-commit install

.. _pyenv: https://github.com/pyenv/pyenv
.. _pyenv-virtualenv: https://github.com/pyenv/pyenv-virtualenv
.. _Fork: https://github.com/crazytruth/iniesta/fork
.. _Clone: https://help.github.com/en/articles/fork-a-repo#step-2-create-a-local-clone-of-your-fork


Start coding
--------------

-   Create a branch to identify the issue you would like to work on. If
    you're submitting a bug or documentation fix, branch off of the
    latest ".x" branch.

    .. code-block:: text

        $ git fetch origin
        $ git checkout -b your-branch-name origin/1.1.x

    If you're submitting a feature addition or change, branch off of the
    "master" branch.

    .. code-block:: text

        $ git fetch origin
        $ git checkout -b your-branch-name origin/master

-   Using your favorite editor, make your changes,
    `committing as you go`_.
-   Include tests that cover any code changes you make. Make sure the
    test fails without your patch. Run the tests as described below.
-   Push your commits to your fork on GitHub and
    `create a pull request`_. Link to the issue being addressed with
    ``fixes #123`` in the pull request.

    .. code-block:: text

        $ git push --set-upstream fork your-branch-name

.. _committing as you go: https://dont-be-afraid-to-commit.readthedocs.io/en/latest/git/commandlinegit.html#commit-your-changes
.. _create a pull request: https://help.github.com/en/articles/creating-a-pull-request


Running the tests
--------------------

Run the basic test suite with pytest.

.. code-block:: text

    $ pytest

This runs the tests for the current environment, which is usually
sufficient. CI will run the full suite when you submit your pull
request. You can run the full test suite with tox if you don't want to
wait.

.. code-block:: text

    $ tox


Running test coverage
--------------------------

Generating a report of lines that do not have test coverage can indicate
where to start contributing. Run ``pytest`` using ``coverage`` and
generate a report.

.. code-block:: text

    $ pip install coverage
    $ coverage run -m pytest
    $ coverage html

Open ``htmlcov/index.html`` in your browser to explore the report.

Read more about `coverage <https://coverage.readthedocs.io>`__.


Building the docs
--------------------

Build the docs in the ``docs`` directory using Sphinx.

.. code-block:: text

    $ cd docs
    $ make html

Open ``build/html/index.html`` in your browser to view the docs.

Read more about `Sphinx <https://www.sphinx-doc.org/en/stable/>`__.

To recompile requirements
-------------------------

All requirements for development, tests, and documentation are
in :code:`requirements` directory.

To recompile requirements. Add the requirements to :code:`*.in`

.. code-block::

    $ cd requirements
    $ pip-compile dev.in
