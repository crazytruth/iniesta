from enum import IntFlag


class InitializationTypes(IntFlag):
    """
    Different initialization types and combinations.
    """

    QUEUE_POLLING = 1  #: 0001 = 1
    EVENT_POLLING = 2  #: 0010 = 2

    SNS_PRODUCER = 16  #: 10000 = 16
    CUSTOM = 32  #: 100000 = 32
