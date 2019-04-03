.. :changelog:

History
-------

0.1.5 (unreleased)
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
