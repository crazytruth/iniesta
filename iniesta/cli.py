# -*- coding: utf-8 -*-

"""Main module."""

import asyncio
import click
import importlib
import logging
import json
import sys
import os

from insanic.conf import settings
from insanic.conf import LazySettings

from iniesta import Iniesta
from iniesta.choices import InitializationTypes
from iniesta.sns import SNSClient
from iniesta.sqs import SQSClient

logger = logging.getLogger(__name__)


@click.group()
def cli():
    logging.disable(logging.CRITICAL)
    sys.path.insert(0, "")


def mock_application(service_name=None):
    service_name = service_name or os.getcwd().split("/")[-1].split("-")[-1]
    config = importlib.import_module(f"{service_name}.config")

    # service_settings = {c: getattr(config, c) for c in dir(config) if c.isupper()}
    # service_settings.update({"INIESTA_DRY_RUN": True})
    config.INIESTA_DRY_RUN = True

    new_settings = LazySettings()
    new_settings.configure(config)

    Iniesta.load_config(new_settings)

    class Dummy:
        config = None

    dummy = Dummy()
    dummy.config = new_settings

    with open(f"{service_name}/app.py", "r") as file:
        for line in file:
            if "Insanic(" in line:
                variable_name = line.split("=")[0].strip()
                exec(f"{variable_name} = dummy")
            elif line.startswith("Iniesta."):
                exec(line)
                break

    return dummy


def get_loaded_config():
    from insanic.exceptions import ImproperlyConfigured

    temp_settings = LazySettings()
    try:
        service_name = temp_settings._infer_app_name()
    except ImproperlyConfigured:
        service_name = os.getcwd().split("/")[-1].split("-")[-1]

    config = importlib.import_module(f"{service_name}.config")

    temp_settings.configure(config)
    # Iniesta.load_config(temp_settings)
    return temp_settings


@cli.command()
def initialization_type():
    temp_settings = get_loaded_config()
    initialization_type = InitializationTypes(0)
    for it in temp_settings.INIESTA_INITIALIZATION_TYPE:
        initialization_type |= InitializationTypes[it]

    print(initialization_type)


@cli.command()
def filter_policies():
    app = mock_application()
    from iniesta.utils import filter_list_to_filter_policies

    # policies = filter_list_to_filter_policies(app.config.INIESTA_SNS_EVENT_KEY,
    #                                           app.config.INIESTA_SQS_CONSUMER_FILTERS)
    policies = filter_list_to_filter_policies(
        app.config.INIESTA_SNS_EVENT_KEY,
        app.config.INIESTA_SQS_CONSUMER_FILTERS,
    )
    print(json.dumps(policies))


@cli.command()
@click.option(
    "-e", "--event", required=True, type=str, help="Event to publish into SNS"
)
@click.option(
    "-m",
    "--message",
    required=False,
    type=str,
    help="Message body to publish into SNS",
)
@click.option(
    "-v",
    "--version",
    required=False,
    type=int,
    help="Version to publish into SNS",
)
def publish(event, message, version):
    # TODO: documentation for read me

    # app = mock_application()
    loop = asyncio.get_event_loop()
    Iniesta.load_config(settings)

    version = version or 1
    message = message or {}

    sns_client = SNSClient()

    message = sns_client.create_message(
        event=event, message=message, version=version, raw_event=True
    )
    # message.add_event(event, raw=True)
    result = loop.run_until_complete(message.publish())

    if result["ResponseMetadata"]["HTTPStatusCode"] == 200:
        click.echo("Publish Success!")
    else:
        click.echo("Publish Failed!")
    click.echo("\n")
    click.echo("REQUEST INFO")
    click.echo(f"Message Event : {message.event}")
    click.echo(f"Message Data : {message.message}")
    click.echo(f"Full Payload : {message}")
    click.echo(f"Message Length : {message.size}")
    click.echo("\n")
    click.echo("RESPONSE INFO")
    click.echo(f"Message ID : {result['MessageId']}")
    click.echo(
        f"Message Length : {result['ResponseMetadata']['HTTPHeaders']['content-length']}"
    )

    Iniesta.unload_config(settings)


@cli.command()
@click.option(
    "-m",
    "--message",
    required=False,
    type=str,
    help="Message body to publish to SQS",
)
def send(message):
    # TODO: documentation for read me

    Iniesta.load_config(settings)

    message = message or {}

    loop = asyncio.get_event_loop()
    sqs_client = loop.run_until_complete(SQSClient.initialize())
    message = sqs_client.create_message(message=message)
    loop.run_until_complete(message.send())

    click.echo("Message Sent")
    click.echo(f"MessageId: {message.message_id}")

    Iniesta.unload_config(settings)
