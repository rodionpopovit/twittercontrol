import pytz

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from .tweetprov.util import TWEET_MESSAGE_LENGTH

# Create your models here.
class Community(models.Model):
    name = models.CharField(max_length=100)
    schema = models.CharField(max_length=150, default='.')

    def __str__(self):
        return self.name

    @property
    def hasTweets(self):
        return len(self.tweets) > 0

    @property
    def tweets(self):
        return TweetMsg.objects.filter(community=self)

class TriggerFrequency(models.Model):
    frequency = models.CharField(max_length=50)
    days = models.SmallIntegerField(editable=True)

    def __str__(self):
        return self.frequency

class TriggerRule(models.Model):
    title = models.CharField(max_length=100)
    rule = models.SmallIntegerField(editable=True, unique=True)

    def __str__(self):
        return self.title

class TweetMsg(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    frequency = models.ForeignKey(TriggerFrequency, on_delete=models.CASCADE, null=True)
    rule = models.ForeignKey(TriggerRule, on_delete=models.CASCADE)
    message = models.CharField(max_length=140)
    last_checked = models.DateTimeField('Last performed', null=True)
    start_date = models.DateTimeField('First trigger at this date', null=True)
    passed_start_date = models.BooleanField(default=True)

    def __str__(self):
        return self.message

    def to_string(self):
        return 'MESSAGE[{}]\nCOMMUNITY[{}]\nFREQUENCY[{}]\nRULE[{}]'.format(
            self.message, self.community, self.frequency, self.rule
        )

    def set_start_date(self, date_input, usr_tz):
        if date_input is None:
            self.start_date = timezone.now()
            self.passed_start_date = False
            return

        try:
            date, time = date_input.split(' ')
            month, day, year = date.split('/')
            hour, minute = time.split(':')

            s_date = timezone.datetime(year=int(year), month=int(month), day=int(day),
                                       hour=int(hour), minute=int(minute))

            if usr_tz is not None:
                tz = pytz.timezone(usr_tz)
                t = tz.localize(s_date)
                s_date = t.astimezone(pytz.utc)

            self.start_date = s_date
            print('setting time to: ', self.start_date)
            print('current timezone: ', usr_tz)
            self.passed_start_date = False
        except ValueError as err:
            print('Encountered error while setting start date')
            print(err)
            self.passed_start_date = True

    @property
    def should_check(self):
        if not self.passed_start_date and self.start_date is not None:
            return timezone.now() >= self.start_date

        if self.last_checked is None:
            return True
        else:
            return timezone.now() >= self.last_checked + timezone.timedelta(days=self.frequency.days)

    def checked_now(self):
        self.last_checked = timezone.now()
        self.passed_start_date = True

    def reset_checked_state(self):
        self.last_checked = None
        self.passed_start_date = False

    @property
    def next_trigger(self):
        if not self.passed_start_date:
            return self.start_date.strftime('%d, %b %Y')

        if self.last_checked is None:
            return 'Now'
        else:
            next_date = self.last_checked + timezone.timedelta(days=self.frequency.days)
            return next_date.strftime('%d, %b %Y')

    def next_trigger_web_format(self, tz):
        if not self.passed_start_date:
            return self.start_date.astimezone(pytz.timezone(tz)).strftime('%x %H:%M')

        if self.last_checked is None:
            return timezone.now().astimezone(pytz.timezone(tz)).strftime('%x %H:%M')
        else:
            next_date = self.last_checked + timezone.timedelta(days=self.frequency.days)
            return next_date.astimezone(pytz.timezone(tz)).strftime('%x %H:%M')

class DatabaseSettings(models.Model):
    hostname = models.CharField(max_length=200)
    dbname = models.CharField(max_length=200)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=50)

    def __str__(self):
        return self.dbname + '@' + self.hostname

    def isValid(self):
        return self.hostname != '' and self.dbname != '' and self.username != ''

class TwitterSettings(models.Model):
    consumer_key = models.CharField(max_length=100)
    consumer_secret = models.CharField(max_length=100)
    access_token = models.CharField(max_length=100)
    access_token_secret = models.CharField(max_length=100)

    def isValid(self):
        return self.consumer_key != '' and self.consumer_secret != '' and self.access_token != '' and self.access_token_secret != ''

class HistoryData(models.Model):
    company_id = models.IntegerField()
    category_id = models.IntegerField()
    ranking = models.IntegerField()
    tweet_id = models.ForeignKey(TweetMsg, on_delete=models.CASCADE)

    def __str__(self):
        return '{co_id} - {tw_id} - {ca_id} - {score}'.format(self.company_id, self.tweet_id, self.category_id, self.ranking)

class TweetLogEntry(models.Model):
    tweet = models.IntegerField(null=True)
    message = models.CharField(max_length=TWEET_MESSAGE_LENGTH)
    date = models.DateTimeField('Time when this message was posted')
    error_message = models.CharField(max_length=200, null=True)

    def setdate(self, date=None):
        if date is None:
            self.date = timezone.now()
        else:
            self.date = date

    def __str__(self):
        return '{} set on date: {}'.format(self.message, self.date)

    def get_formatted_date(self, tz):
        if self.date is not None:
            if tz is not None:
                return self.date.astimezone(pytz.timezone(tz))
            else:
                return self.date

class TweetsQueueMember(models.Model):
    tweet = models.ForeignKey(TweetMsg, on_delete=models.CASCADE)
    message = models.CharField(max_length=TWEET_MESSAGE_LENGTH)

    def __str__(self):
        return '{}'.format(self.message)

class UserData(models.Model):
    user = models.ForeignKey(User)
    tz = models.CharField(max_length=100)

    @property
    def zone(self):
        if '/' in self.tz:
            return self.tz.split('/')[0]
        else:
            return self.tz

    @property
    def state(self):
        if '/' in self.tz:
            return self.tz.split('/')[1]
        else:
            return ''

    def setfromparts(self, zone, state):
        full = '/'.join((zone, state))
        if self.tz != full:
            self.tz = full