from django.conf.urls import url

from . import views

app_name = 'tpw'
urlpatterns = [
    url(r'^login/$', views.loginview, name='login'),
    url(r'^logout/$', views.logoutview, name='logout'),
    url(r'^authenticate/$', views.authenticationview, name='authenticate'),
    url(r'^account/$', views.changeuserdata, name='account'),
    url(r'^account/(?P<msg>[0-9a-zA-Z _]*)/$', views.changeuserdata, name='account'),
    url(r'^validateaccountupdate/$', views.validateaccountupdate, name='validateaccountupdate'),
    url(r'^$', views.index, name='index'),
    url(r'^(?P<tweet_id>[0-9]+)/$', views.viewtweet, name='viewtweet'),
    url(r'^list/$', views.listtweets, name='listtweets'),
    url(r'^add/$', views.addtweet, name='addtweet'),
    url(r'^edit/(?P<tweet_id>[0-9]+)/$', views.edittweet, name='edittweet'),
    url(r'^resettweet/$', views.resettweet, name='resettweet'),
    url(r'^testtweet/$', views.testtweet, name='testtweet'),
    url(r'^update/(?P<tweet_id>[0-9]+)/$', views.updatetweet, name='updatetweet'),
    url(r'^delete/(?P<tweet_id>[0-9]+)/$', views.deletetweet, name='deletetweet'),
    url(r'^config/$', views.editconfig, name='config'),
    url(r'^configupdate/$', views.updateconfig, name='updateconfig'),
    url(r'^querytokens/$', views.getavailabletags, name='querytokens'),
    url(r'^tweetslog/$', views.showlogs, name='tweetslog'),
    url(r'^tweetslogcontent/$', views.showlogscontent, name='tweetslogcontent'),
    url(r'^cleartweetslog/$', views.clearlogs, name='cleartweetslog'),
    url(r'^outbox/$', views.viewoutbox, name='outbox'),
    url(r'^outboxcontent/$', views.viewoutboxcontent, name='outboxcontent'),
    url(r'^resendtweet/$', views.resendTweet, name='resendtweet'),
    url(r'^pausesending/$', views.pausesending, name='pausesending'),
    url(r'^getcountrytimezones/(?P<zone>[0-9a-zA-Z]+)/$', views.getcountryzones, name='getcountrytimezones'),
]
