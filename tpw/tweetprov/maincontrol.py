import logging
import sys
import time
import argparse

from .util import LOGGER_NAME, EVAL_TIMEOUT, TWEET_POST_TIMEOUT, singleton
from .util import RULE_TOP_3, RULE_BOTTOM_3, RULE_NO_PROV_SCORE
from .configuration import ConfigurationManager
from .dbmanager import DBManager, DBException
from .messageformat import formatMessage, FormattingError
from .twittercontrol import TwitterControl, TwitterException
from .twittercontrol import TP_OK, TP_RATE_LIMIT, TP_UNKNOWN, TP_NOT_LOGGED_IN

from tpw.models import TweetMsg, Community, TweetsQueueMember, TweetLogEntry


@singleton
class Proven:
    def __init__(self):
        self.__allGood = False # start pessimistic

        self.logger = logging.getLogger(LOGGER_NAME)
        self.cfg = ConfigurationManager()

        self.db = None
        self.twitter = None
        self.__runTasks = True
        self.__lastMessagePostedAt = 0
        self.__waitTime = TWEET_POST_TIMEOUT
        self.__atRateLimit = False
        self.__sending = True

    def initialize(self):
        try:
            self.db = DBManager(self.cfg)
            self.twitter = TwitterControl(self.cfg, fake=True)

            if not self.twitter.login():
                self.logger.error('Failed to login to twitter')
        except DBException as err:
            self.logger.error('Failed to connect to database')
            self.logger.debug(str(err))
        except TwitterException as err:
            self.logger.error('Failed to connect to Twitter account')
            self.logger.debug(str(err))
        else:
            self.logger.info('Connections established')

        self.__allGood = True # everything is fine

    def __evaluate(self):
        ### check for tweet generation ###
        for tweet in TweetMsg.objects.all():
            if tweet.should_check:
                if tweet.community.schema in self.db.companies:
                    try:
                        for message in formatMessage(self.db, tweet):
                            m = TweetsQueueMember()
                            m.message = message
                            m.tweet = tweet
                            m.save()

                        tweet.checked_now()
                        tweet.save()
                    except FormattingError: # skip incorrectly formatted tweet
                        continue

        if not self.__sending:
            return

        ### check for tweet posting ###
        if not self.dbConnected or not self.twitterConnected or self.__lastMessagePostedAt + self.__waitTime >= time.time():
            return

        msg = TweetsQueueMember.objects.first()

        if msg is None:
            return

        status, message = self.twitter.postMessage(msg.message)

        if status == TP_RATE_LIMIT:
            self.__atRateLimit = True

            if self.__waitTime < 1000:
                self.__waitTime *= 2

            return
        elif status == TP_UNKNOWN:
            self.logPostedMessage(msg.message, msg.tweet.id, message)
            msg.delete()
        elif status == TP_OK:
            self.logPostedMessage(msg.message, msg.tweet.id)
            msg.delete()

            self.__lastMessagePostedAt = time.time()
        elif status == TP_NOT_LOGGED_IN:
            return

        self.__waitTime = TWEET_POST_TIMEOUT
        self.__atRateLimit = False

    def testTweet(self, rule, comName, comSchema, message):
        class FakeTweet:
            def __init__(self, ruleId, cName, sch, msg):
                class Dummy:
                    pass

                self.rule = Dummy()
                self.community = Dummy()

                self.rule.rule = ruleId
                self.community.name = cName
                self.community.schema = sch
                self.message = msg

        if not self.dbConnected:
            return None

        try:
            messages = list(formatMessage(self.db, FakeTweet(rule, comName, comSchema, message), override=True))
            return len(messages), messages
        except FormattingError:
            raise

    def stop(self, _, __): # ignore parameters sent by signal.signal
        self.__runTasks = False

    def run(self):
        time.sleep(3) # delay start

        self.initialize()

        while self.__runTasks:
            try:
                communities = Community.objects.all()

                if communities is not None:
                    self.db.refreshData((com.schema for com in communities))
                    self.__evaluate()
            except DBException as err:
                print('Problems with loading data', str(err))
                self.logger.debug(str(err))

            time.sleep(EVAL_TIMEOUT)

    def pauseSending(self):
        self.__sending = not self.__sending
        return self.__sending

    @property
    def isSending(self):
        return self.__sending

    @property
    def isAtRateLimit(self):
        return self.__atRateLimit

    @property
    def currentWaitTime(self):
        return self.__waitTime

    @property
    def initialized(self):
        return self.__allGood

    @staticmethod
    def logPostedMessage(message, tweetId, errorMessage=None):
        tle = TweetLogEntry(message=message, tweet=tweetId, error_message=errorMessage)
        tle.setdate()
        tle.save()

        allLogs = TweetLogEntry.objects.order_by('id')

        if len(allLogs) > 20:
            allLogs[0].delete()

    @staticmethod
    def getTags(ruleId):
        if ruleId in (RULE_TOP_3, RULE_BOTTOM_3):
            return '{companyname1} {companyname2} {companyname3} {categoryname} {categoryurl} ' +\
                    '{nrofcompanies} {companies} {profileurl1} {profileurl2} {profileurl3} ' +\
                    '{location1} {location2} {location3} {score1} {score2} {score3} ' +\
                    '{domain} {domainurl}'
        elif ruleId == RULE_NO_PROV_SCORE:
            return '{companyname} {categoryname} {profileurl} {location} {categoryurl} {domain} {domainurl}'
        else:
            return '{companyname} {categoryname} {profileurl} {location} {score} {categoryurl} {domain} {domainurl}'

    @property
    def dbConnected(self):
        if self.db is None: return False
        return self.db.isConnected
    
    @property
    def twitterConnected(self):
        if self.twitter is None: return False
        return self.twitter.isConnected
