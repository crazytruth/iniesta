####################### SNS/SQS

# SNS_INITIALZE_HARD_FAILURE = False
# SNS_PUBLISH_HARD_FAILURE = False

SNS_PRODUCER_GLOBAL_TOPIC_ARN = None

SQS_RECEIVE_MESSAGE_MAX_NUMBER_OF_MESSAGES = 10 # values needs to be 0-10
SQS_RECEIVE_MESSAGE_WAIT_TIME_SECONDS = 20 # needs to be a value between 0-20 (0 for short polling)

SQS_QUEUE_DEFAULT_ATTRIBUTES = {
    "DelaySeconds": None, # Min: 0 Max: 900(5 mins) Default: 0
    "MaximumMessageSize": None, # Min: 1024 Max: 262144 Default: 262144 (245KiB)
    "MessageRetentionPeriod": None, # Min: 60(1 min) Max: 1,209,600 (14 days) Default: 345,600 (4 days)
    "ReceiveMessageWaitTimeSeconds": None, # Min: 0 Max: 20 seconds Default: 0
    "VisibilityTimeout": None, # 0-43200 Default: 30
}

SQS_CONSUMER_FILTERS = {
    "UserRequestedThroughIP": {},
}

SNS_DOMAIN_EVENT_KEY = 'insanic_event'

