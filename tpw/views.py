import pytz

from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import Http404
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import TweetMsg, Community, TriggerFrequency, TriggerRule, TweetsQueueMember
from .models import DatabaseSettings, TwitterSettings, HistoryData, TweetLogEntry
from .models import UserData

from .tweetprov.maincontrol import Proven
from .tweetprov.messageformat import FormattingError
from .tweetprov.util import RULE_NO_1


def loginview(request):
    referer = '/tweetcontrol/'

    if 'HTTP_REFERER' in request.META:
        referer = request.META['HTTP_REFERER']

    if 'next' in request.GET:
        referer = request.GET['next']

    return render(request, 'tpw/login.html', {
        'referer': referer,
        'error': None,
    })

def logoutview(request):
    logout(request)
    return HttpResponseRedirect(reverse('tpw:index'))

def authenticationview(request):
    try:
        username = request.POST['username']
        password = request.POST['password']

        try:
            ref = request.POST['referer']
        except KeyError:
            ref = '/tweetcontrol/'

        user = authenticate(username=username,
                            password=password)

        if user is not None: # authentication worked
            login(request, user)
            return HttpResponseRedirect(ref)
        else:
            return render(request, 'tpw/login.html', {
                'referer': ref,
                'error': 'Failed to authenticate you'
            })
    except KeyError:
        return HttpResponseRedirect(reverse('tpw:login'))

def index(request):
    tweets = TweetMsg.objects.all()

    context = {
        'tweets_list': tweets,
        'authenticated': request.user.is_authenticated,
    }

    return render(request, 'tpw/index.html', context)

@login_required
def editconfig(request):
    db = DatabaseSettings.objects.first()
    tw_account = TwitterSettings.objects.first()

    context = {
        'message': messages.get_messages(request),
        'database': db,
        'tw_account': tw_account
    }

    return render(request, 'tpw/editconfig.html', context)

@login_required
def updateconfig(request):
    db = DatabaseSettings.objects.first()
    tw_account = TwitterSettings.objects.first()

    if db is None:
        db = DatabaseSettings()

    if tw_account is None:
        tw_account = TwitterSettings()

    try:
        db.hostname = request.POST['databasehosttxt']
        db.dbname = request.POST['databasenametxt']
        db.username = request.POST['databaseusertxt']
        db.password = request.POST['databasepasstxt']

        db.save()

        tw_account.consumer_key = request.POST['consumerkeytxt']
        tw_account.consumer_secret = request.POST['consumersecrettxt']
        tw_account.access_token = request.POST['accesstokentxt']
        tw_account.access_token_secret = request.POST['accesstokensecrettxt']

        tw_account.save()

        messages.add_message(request, messages.INFO, 'Configuration saved!')
        return HttpResponseRedirect(reverse('tpw:config'))
    except KeyError:
        messages.add_message(request, messages.ERROR, 'Failed to save configuration')
        return HttpResponseRedirect(reverse('tpw:config'))

@login_required
def viewoutbox(request):
    return render(request, 'tpw/outbox.html')

@login_required
def viewoutboxcontent(request):
    proven = Proven()

    return render(request, 'tpw/outboxcontent.html', {
        'outbox': TweetsQueueMember.objects.order_by('id'),
        'ratelimit': proven.isAtRateLimit,
        'timeout': proven.currentWaitTime,
        'isrunning': proven.isSending,
    })

@login_required
def resettweet(request):
    try:
        tweet_id = int(request.GET['tweet'])
        tweet = TweetMsg.objects.get(pk=tweet_id)
        tweet.reset_checked_state()
        tweet.save()

        if tweet.rule.rule == RULE_NO_1:
            HistoryData.objects.filter(tweet_id=tweet_id).delete()

        return HttpResponse('Tweet {} has been reset'.format(tweet_id))
    except (KeyError, ValueError, TweetMsg.DoesNotExist):
        return HttpResponse('Failed to reset tweet {}'.format(tweet_id))

@login_required
def viewtweet(request, tweet_id):
    tweet = get_object_or_404(TweetMsg, pk=tweet_id)
    return render(request, 'tpw/viewtweet.html', {'tweet': tweet})

@login_required
def listtweets(request):
    p = Proven()

    try:
        ud = UserData.objects.get(user=request.user)
        tz = ud.tz
    except UserData.DoesNotExist:
        tz = None

    tweets = TweetMsg.objects.order_by('-id')

    for t in tweets:
        t.formatted_next_trigger = t.next_trigger_web_format(tz)

    return render(request, 'tpw/listtweets.html', {
        'tweets_list': tweets,
        'communities_list': Community.objects.order_by('name'),
        'dbconnected': p.dbConnected,
        'tweetconnected': p.twitterConnected,
    })

@login_required
def resendTweet(request):
    try:
        entryId = int(request.GET['tweet'])
        entry = get_object_or_404(TweetLogEntry, pk=entryId)

        try:
            tweet = TweetMsg.objects.get(pk=entry.tweet)
            tqm = TweetsQueueMember(tweet=tweet, message=entry.message)
            tqm.save()
        except TweetMsg.DoesNotExist:
            return HttpResponse('Tweet corresponding to log probably deleted')

        entry.delete()

        return HttpResponse('Tweet resent')
    except (KeyError, ValueError):
        return Http404('Missing identifier in GET request')

@login_required
def showlogs(request):
    return render(request, 'tpw/tweetslog.html')

@login_required
def showlogscontent(request):
    entries = TweetLogEntry.objects.order_by('-id')

    try:
        ud = UserData.objects.get(user=request.user)
        tz = ud.tz
    except UserData.DoesNotExist:
        tz = None

    for e in entries:
        e.formatted_date = e.get_formatted_date(tz).strftime('%b. %d, %y, %H:%M %P')

    return render(request, 'tpw/tweetslogcontent.html', {
        'log': entries,
    })

@login_required
def clearlogs(request):
    TweetLogEntry.objects.all().delete()
    return HttpResponse('Log cleared')

@login_required
def addtweet(request):
    tweet = None
    communities = Community.objects.all()
    frequencies = TriggerFrequency.objects.all()
    rules = TriggerRule.objects.all()

    return render(request, 'tpw/addtweet.html', {
        'tweet_id': 0,
        'tweet': tweet,
        'communities': communities,
        'frequencies': frequencies,
        'rules': rules,
    })

@login_required
def getavailabletags(request):
    FORMAT_COLS_PER_LINE = 3

    if request.method == 'GET':
        try:
            rule_id = int(request.GET['rule'])
            val = TriggerRule.objects.get(pk=rule_id).rule

            rawTags = Proven().getTags(val).split(' ')

            finalTags = '<table>'
            for i in range(0, len(rawTags), FORMAT_COLS_PER_LINE):
                finalTags += '<tr>'
                for j in range(i, min(len(rawTags), i + FORMAT_COLS_PER_LINE)):
                    finalTags += '<td onclick="addTag(\'' + rawTags[j] + '\')">' + rawTags[j] + '</td>'
                finalTags += '</tr>'
            finalTags += '</table>'

            return HttpResponse(finalTags)
        except (KeyError, ValueError):
            pass

    return HttpResponse('Failed to get tags')

@login_required
def edittweet(request, tweet_id):
    tweet = get_object_or_404(TweetMsg, pk=tweet_id)
    communities = Community.objects.all()
    frequencies = TriggerFrequency.objects.all()
    rules = TriggerRule.objects.all()

    try:
        ud = UserData.objects.get(user=request.user)
        tz = ud.tz
    except UserData.DoesNotExist:
        tz = None

    tweet.formatted_next_trigger = tweet.next_trigger_web_format(tz)

    return render(request, 'tpw/addtweet.html', {
        'tweet_id': tweet_id,
        'tweet': tweet,
        'communities': communities,
        'frequencies': frequencies,
        'rules': rules,
        'timezone': tz,
    })

@login_required
def testtweet(request):
    try:
        rule_id = int(request.GET['rule'])
        com_id = int(request.GET['community'])
        msg = request.GET['message']
        date = request.GET['date']

        community = Community.objects.get(pk=com_id)
        rule = TriggerRule.objects.get(pk=rule_id).rule

        result = Proven().testTweet(rule, community.name, community.schema, msg)

        if result is None:
            raise ValueError()

        RESULTS_LIMIT = 10
        return render(request, 'tpw/testtweet.html', {
            'length': result[0],
            'messages': result[1][:RESULTS_LIMIT],
            'limit': RESULTS_LIMIT,
            'date': date,
        })
    except (KeyError, ValueError):
        return HttpResponse('Failed to test tweet. Communication error.')
    except FormattingError as err:
        return HttpResponse(err.args[0])

@login_required
def updatetweet(request, tweet_id):
    try:
        tweet = TweetMsg.objects.get(pk=tweet_id)
    except TweetMsg.DoesNotExist:
        tweet = TweetMsg()

    try:
        try:
            usr = UserData.objects.get(user=request.user)
            tz = usr.tz
        except UserData.DoesNotExist:
            tz = None

        tweet.message = request.POST['requiredmessage']
        tweet.community = Community.objects.get(id=int(request.POST['communityoption']))
        tweet.frequency = TriggerFrequency.objects.get(id=int(request.POST['frequencyoption']))
        tweet.rule = TriggerRule.objects.get(id=int(request.POST['ruleoption']))
        tweet.set_start_date(request.POST['startdate'], tz)
        tweet.save()

        return HttpResponseRedirect(reverse('tpw:listtweets'))
    except KeyError:
        return HttpResponse('Invalid usage')

@login_required
def deletetweet(request, tweet_id):
    try:
        tweet = TweetMsg.objects.get(pk=tweet_id)
        tweet.delete()
    except TweetMsg.DoesNotExist:
        pass

    return HttpResponseRedirect(reverse('tpw:listtweets'))

@login_required
def pausesending(request):
    Proven().pauseSending()
    return HttpResponse('Sent pause request')

def getallzones():
    result = set()

    for z in pytz.all_timezones:
        if '/' in z:
            current = z.split('/')[0]
        else:
            current = z

        result.add(current)

    return sorted(result)

def getstatesforzone(zone):
    result = set()

    for z in pytz.all_timezones:
        if (zone + '/') in z:
            result.add(''.join(z.split('/')[1:]))

    return sorted(result)

@login_required
def changeuserdata(request, msg=None):
    u = request.user

    try:
        d = UserData.objects.get(user=u)
        userzone = d.zone
        userstate = d.state
    except UserData.DoesNotExist:
        userzone = 'US'
        userstate = 'Central'

    return render(request, 'tpw/usersettings.html', {
        'username': u.username,
        'userzone': userzone,
        'userstate': userstate,
        'zones': getallzones(),
        'states': getstatesforzone(userzone),
        'errormsg': msg,
    })

@login_required
def getcountryzones(request, zone):
    i = 0
    r = '<select>'
    for c in getstatesforzone(zone):
        r += '<option value="{}">{}</option>'.format(c, c)
    r += '</select>'

    return HttpResponse(r)

@login_required
def validateaccountupdate(request):
    try:
        stzdata = request.POST['stzdata']
        stzstate = request.POST['stzstate']
        txtnewpass = request.POST['txtnewpass'].strip()
        txtoldpass = request.POST['txtoldpass'].strip()
        txtrepeatpass = request.POST['txtpassrepeat'].strip()

        try:
            data = UserData.objects.get(user=request.user)
        except UserData.DoesNotExist:
            data = UserData(user=request.user)

        data.setfromparts(stzdata, stzstate)
        if txtnewpass != '':
            if txtnewpass == txtrepeatpass:
                if request.user.check_password(txtoldpass):
                    request.user.set_password(txtnewpass)
                    request.user.save()
                    return HttpResponseRedirect(reverse('tpw:account', kwargs={'msg':'Success'}))
                else:
                    return HttpResponseRedirect(reverse('tpw:account', kwargs={'msg':'Invalid credentials'}))
            else:
                return HttpResponseRedirect(reverse('tpw:account', kwargs={'msg':'Please enter all relevant fields'}))

        data.save()
    except KeyError as err:
        print(err)
        return HttpResponseRedirect(reverse('tpw:account', kwargs={'msg':'Failed'}))

    return HttpResponseRedirect(reverse('tpw:account', kwargs={'msg':'Success'}))