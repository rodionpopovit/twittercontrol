import logging

from .configuration import ConfigurationManager
from .util import LOGGER_NAME

from tpw.models import HistoryData


class HistoryManager:
    """
    Handles relevant task scheduling and saving persistent data
    """

    def __init__(self, cfg: ConfigurationManager):
        self.__cfgManager = cfg
        self.__logger = logging.getLogger(LOGGER_NAME)

    # persistent storage #

    @staticmethod
    def getHistoryFor(_id, tweetId):
        try:
            return HistoryData.objects.get(company_id=_id, tweet_id=tweetId)
        except HistoryData.DoesNotExist:
            return None

    @staticmethod
    def saveHistoryFor(_id, ranking, category, tweet):
        try:
            hd = HistoryData.objects.get(company_id=_id, tweet_id=tweet.id)
        except HistoryData.DoesNotExist:
            hd = HistoryData()

        hd.company_id = _id
        hd.category_id = category
        hd.ranking = ranking
        hd.tweet_id = tweet

        hd.save()
