.. :changelog:

History
-------

0.3.4 (2020-04-02)
++++++++++++++++++

- CHORE: update for aiobotocore>=0.12.0


0.3.3 (2020-03-18)
++++++++++++++++++

- FEAT: allow add_handler method to bind multiple events to one handler


0.3.2 (2019-09-26)
++++++++++++++++++

- FIX: issue in cli where service_name wasn't being parsed properly


0.3.1 (2019-09-25)
++++++++++++++++++

- FIX: issue when settings doesn't have access to vault #51
- CHORE: adds test for filter policy command


0.3.0 (2019-07-31)
++++++++++++++++++

- BREAKING: removed all `prepare_*` initialization methods. They were confusing me.
- BREAKING: removed all `init_*` other than `init_app`
- BREAKING: must include `INIESTA_INITIALIZATION_TYPE` in your config.
- CHORE: refactors initialization-type command to use `INIESTA_INITIALIZATION_TYPE` settings
- CHORE: updates Click requirement to 7.0 or higher

0.2.5 (2019-07-29)
++++++++++++++++++

- FIX: fixes initialization-type command to not check resources


0.2.4 (2019-07-26)
++++++++++++++++++

- FIX: fixes initialization-type command to bypass vault configuration


0.2.3 (2019-07-12)
++++++++++++++++++

- FEAT: add init_custom helper method to Iniesta
- FEAT: allows region_name and endpoint_url when initializing SNSClient
- FEAT: allows region_name and endpoint_url when initializing SQSClient
- CHORE: documentation about advanced usages
- FIX: typo in iniesta configs REGIO -> REGION


0.2.2 (2019-07-04)
++++++++++++++++++

- FIX: reinstantiate aiobotocore session if loop is not running


0.2.1 (2019-07-03)
++++++++++++++++++

- FIX: reinstantiate aiobotocore session if loop is closed


0.2.0 (2019-07-02)
++++++++++++++++++

- FEAT: allow aws credentials to be loaded from iniesta then fallback to insanic
- FEAT: added `publish_event` decorator for view functions.
- FEAT: allows aws region configurations through settings or environment variables.
- FIX: fixes config issues when using publish cli
- ENHANCEMENT: when publishing with publish cli, it now DOESN'T append the service name.


0.1.7 (2019-04-11)
++++++++++++++++++

- FEAT: allow aws credentials to be loaded from settings. ``INIESTA_AWS_ACCESS_KEY_ID`` and ``INIESTA_AWS_SECRET_ACCESS_KEY``
- CHORE: MO documentations!!!
- CHORE: change extra requires from ``deploy`` to ``cli``
- CHORE: remove used parameters


0.1.6 (2019-04-04)
++++++++++++++++++

- FIX: fixes SQS message so it return None if key doesn't exist
- CHORE: includes various sphinx documentation


0.1.5 (2019-04-04)
++++++++++++++++++

- FEAT: update commands to not explicitly load application


0.1.4 (2019-04-03)
++++++++++++++++++

- REFACTOR: commands to within iniesta package


0.1.2 (2019-04-02)
++++++++++++++++++

- FEAT: separate initialization methods for purposes
- FEAT: allow decorating of default(fallback) handler
- FEAT: attempt to auto json encode sns message
- FEAT: topic arn when initializing defaults to settings
- FEAT: commands for extracting settings ``initialization-type`` and ``filter-policies``
- REFACTOR: changes to clients so the messages do the actual behavior(SNSMessage publishes, SQSMessages sends)
- CHORE: more test coverage
- CHORE: refactor endpoint urls to settings
- CHORE: refactor message attributes from SNSMessage to base class
- FIX: fix when message is not json loadable


0.1.1 (2019-03-22)
++++++++++++++++++

* First release on PyPI.
