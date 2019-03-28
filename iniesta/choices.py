from enum import IntFlag


class InitializationTypes(IntFlag):
    QUEUE_POLLING = 1  # 0001
    EVENT_POLLING = 2  # 0010

    SNS_PRODUCER = 16  # 10000
