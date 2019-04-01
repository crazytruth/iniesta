# -*- coding: utf-8 -*-

"""Main module."""


import click
import importlib
import logging
import json
import sys

from insanic.conf import settings

logger = logging.getLogger(__name__)


@click.group()
def cli():
    logging.disable(logging.CRITICAL)
    sys.path.insert(0, '')

    importlib.import_module(f"{settings.SERVICE_NAME}.app")

@cli.command()
def initialization_type():
    from iniesta import Iniesta
    print(Iniesta.initialization_type)

@cli.command()
def filter_policies():
    from iniesta.utils import filter_list_to_filter_policies
    policies = filter_list_to_filter_policies(settings.INIESTA_SNS_EVENT_KEY,
                                              settings.INIESTA_SQS_CONSUMER_FILTERS)
    print(json.dumps(policies))


