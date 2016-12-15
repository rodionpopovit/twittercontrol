from tpw.models import DatabaseSettings, TwitterSettings


class ConfigurationException(Exception):
    """
    Handle all configuration exceptions
    """
    pass

def checkValidity(fn):
    def _wrapper(*args, **kwargs):
        if not args[0].isValid:
            raise ConfigurationException('Called {} from invalid configuration'.format(fn.__name__))
        else:
            try:
                return fn(*args, **kwargs)
            except Exception as err:
                raise ConfigurationException(err.args[0])

    return _wrapper

class ConfigurationManager:
    def __init__(self):
        self.__initNotStarted = True
        self.__dbSettings = None
        self.__tweetSettings = None

    @property
    def isValid(self):
        if self.__initNotStarted:
            self.__dbSettings = DatabaseSettings.objects.first()
            self.__tweetSettings = TwitterSettings.objects.first()

        if self.__dbSettings is None or self.__tweetSettings is None:
            return False

        if not self.__dbSettings.isValid() or not self.__tweetSettings.isValid():
            return False

        self.__initNotStarted = False
        return True

    ## methods to get data from .ini ##

    @property
    @checkValidity
    def databaseSettings(self):
        return (self.__dbSettings.hostname, self.__dbSettings.dbname,
                self.__dbSettings.username, self.__dbSettings.password)

    @property
    @checkValidity
    def twitterDevData(self):
        return (self.__tweetSettings.consumer_key, self.__tweetSettings.consumer_secret,
                self.__tweetSettings.access_token, self.__tweetSettings.access_token_secret)
