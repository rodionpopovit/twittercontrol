import tweepy
import random

from .configuration import ConfigurationException


TP_OK = 0
TP_RATE_LIMIT = 60
TP_UNKNOWN = 2
TP_MSG_TO_LONG = 3
TP_NOT_LOGGED_IN = 4


class TwitterException(Exception):
    """
    Generic exception to handle Twitter API issues
    """
    pass

class TwitterControl:
    """
    Handles all Twitter related interaction
    """

    def __init__(self, cfg, fake = False):
        self.cfg = cfg
        self.__fake = fake

        self.__twitterApi = None
        self.__loggedIn = fake
        self.__lastData = None

    def __actualLogin(self, data):
        auth = tweepy.OAuthHandler(data[0], data[1])
        auth.set_access_token(data[2], data[3])

        api = tweepy.API(auth)

        try:
            api.verify_credentials() # just check if it can perform operation -> logged in

            self.__twitterApi = api
            self.__loggedIn = True
            self.__lastData = data

            return True
        except tweepy.TweepError:
            self.__loggedIn = False
            return False

    def login(self):
        if self.__fake: return True

        try:
            data = self.cfg.twitterDevData
        except ConfigurationException:
            return self.__loggedIn

        if self.__loggedIn:
            if self.__lastData != data:
                return self.__actualLogin(data)
        else:
            self.__actualLogin(data)

        return self.__loggedIn

    def postMessage(self, message):
        if self.__fake:
            val = random.randrange(0, 10)
            errMsg = None
            if val == 0:
                err = TP_RATE_LIMIT
            elif val == 1:
                err = TP_UNKNOWN
                errMsg = 'Testing error'
            else:
                err = TP_OK

            print(message)
            print(err, errMsg)
            print('-------------')
            return err, errMsg

        if self.login():
            try:
                self.__twitterApi.update_status(message)
                return TP_OK, None
            except tweepy.RateLimitError:
                return TP_RATE_LIMIT, None
            except tweepy.TweepError as err:
                if err.args[0][0]['message'].startswith('Status is over '): # message to big
                    return TP_MSG_TO_LONG, 'Message is too long'
                return TP_UNKNOWN, err.args[0][0]
        else:
            return TP_NOT_LOGGED_IN, None

    @property
    def isConnected(self):
        return self.__loggedIn