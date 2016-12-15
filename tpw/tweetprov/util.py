LOGGER_NAME = 'twitter-proven'
CONFIGURATION_FILE_NAME = 'settings.ini'
EVAL_TIMEOUT = 1 # allow 1 second between each evaluation

RULE_NO_1 = 0
RULE_TOP_3 = 1
RULE_BOTTOM_3 = 2
RULE_NO_PROV_SCORE = 3
RULE_AT_SPECIFIC_TIME = 4

TWEET_MESSAGE_LENGTH = 140
TWEET_POST_TIMEOUT = 2

def singleton(cls):
    """Use this decorator to turn a class into singleton"""

    INSTANCES = {}

    def getInstance():
        if cls not in INSTANCES:
            INSTANCES[cls] = cls()

        return INSTANCES[cls]

    return getInstance