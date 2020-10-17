from typing import Optional, Dict, List

#: The redlock caches
INIESTA_CACHES: Dict[str, dict] = {
    "iniesta1": {"HOST": "localhost", "PORT": 6379, "DATABASE": 1},
    "iniesta2": {"HOST": "localhost", "PORT": 6379, "DATABASE": 2},
    "iniesta3": {"HOST": "localhost", "PORT": 6379, "DATABASE": 3},
}

#: The initialization type Iniesta will be initialized with.
INIESTA_INITIALIZATION_TYPE: tuple = tuple()
# ["SNS_PRODUCER", "EVENT_POLLING", "QUEUE_POLLING", "CUSTOM"]

#: The topic arn for the SNS that will receive messages.
INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN: str = None

#: The number of messages to receive while polling. Value between 0-10
INIESTA_SQS_RECEIVE_MESSAGE_MAX_NUMBER_OF_MESSAGES: int = 10

#: The time to wait between receiving SQS messages. A value between 0-20 (0 for short polling).
INIESTA_SQS_RECEIVE_MESSAGE_WAIT_TIME_SECONDS: int = 20

# possible filters:
# if ends with ".*" then filter is concerted to prefix
# reference: https://docs.aws.amazon.com/sns/latest/dg/sns-subscription-filter-policies.html

#: The filters you would like for your application's queue to filter for.
INIESTA_SQS_CONSUMER_FILTERS: List[str] = []

#: If you would like to verify the filter policies on AWS match the filter policies declared in your application.
INIESTA_ASSERT_FILTER_POLICIES: bool = True

#: The event key that will be filtered.
INIESTA_SNS_EVENT_KEY: str = "iniesta_pass"

#: The default sqs queue name
INIESTA_SQS_QUEUE_NAME: Optional[str] = None

#: The SQS queue name template, if you have a normalized queue naming scheme.
INIESTA_SQS_QUEUE_NAME_TEMPLATE: str = "iniesta-{env}-{service_name}"

#: The retry count for attempting to acquire a lock.
INIESTA_LOCK_RETRY_COUNT: int = 1

#: The lock timeout for the message. Will release after defined value.
INIESTA_LOCK_TIMEOUT: int = 10

# mainly used for tests
# INIESTA_SQS_REGION_NAME: Optional[str] = None
INIESTA_SQS_ENDPOINT_URL: Optional[str] = None
#
# INIESTA_SNS_REGION_NAME: Optional[str] = None
INIESTA_SNS_ENDPOINT_URL: Optional[str] = None

INIESTA_DRY_RUN: bool = False

#: Your AWS Access Key if it is different from other access keys.
INIESTA_AWS_ACCESS_KEY_ID = None

#: Your AWS Secret Access Key if it is different from other access keys.
INIESTA_AWS_SECRET_ACCESS_KEY = None

#: Your AWS Default Region if it is iniesta specific
INIESTA_AWS_DEFAULT_REGION: Optional[str] = None
