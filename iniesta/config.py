####################### SNS/SQS

# SNS_INITIALZE_HARD_FAILURE = False
# SNS_PUBLISH_HARD_FAILURE = False

INIESTA_SNS_PRODUCER_GLOBAL_TOPIC_ARN = None

INIESTA_SQS_RECEIVE_MESSAGE_MAX_NUMBER_OF_MESSAGES = 10 # values needs to be 0-10
INIESTA_SQS_RECEIVE_MESSAGE_WAIT_TIME_SECONDS = 20 # needs to be a value between 0-20 (0 for short polling)

# INIESTA_SQS_QUEUE_DEFAULT_ATTRIBUTES = {
#     "DelaySeconds": None, # Min: 0 Max: 900(5 mins) Default: 0
#     "MaximumMessageSize": None, # Min: 1024 Max: 262144 Default: 262144 (245KiB)
#     "MessageRetentionPeriod": None, # Min: 60(1 min) Max: 1,209,600 (14 days) Default: 345,600 (4 days)
#     "ReceiveMessageWaitTimeSeconds": None, # Min: 0 Max: 20 seconds Default: 0
#     "VisibilityTimeout": None, # 0-43200 Default: 30
# }


# possible filters:
# if ends with ".*" then filter is concerted to prefix
# reference: https://docs.aws.amazon.com/sns/latest/dg/sns-subscription-filter-policies.html
INIESTA_SQS_CONSUMER_FILTERS = []

INIESTA_SNS_EVENT_KEY = 'iniesta_pass'

INIESTA_SQS_QUEUE_NAME_TEMPLATE = "iniesta-{env}-{service_name}"

INIESTA_LOCK_RETRY_COUNT = 1
INIESTA_LOCK_TIMEOUT = 10