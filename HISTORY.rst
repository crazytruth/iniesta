.. :changelog:

History
-------

0.1.2 (unreleased)
++++++++++++++++++

- FEAT: separate initialization methods for purposes
- FEAT: allow decorating of default(fallback) handler
- FEAT: attempt to auto json encode sns message
- FEAT: topic arn when initializing defaults to settings
- FEAT: commands for extracting settings `initialization-type` and `filter-policies`
- CHORE: more test coverage
- CHORE: refactor endpoint urls to settings
- CHORE: refactor message attributes from SNSMessage to base class
- FIX: fix when message is not json loadable


0.1.1 (2019-03-22)
++++++++++++++++++

* First release on PyPI.
