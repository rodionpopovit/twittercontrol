------------------------------------------------
Structure
--
Django project: twitterprovenweb
Django app: tpw
App static files: tpw/static/tpw
------------------------------------------------
Dependencies found in requirements.txt
------------------------------------------------
Details:
current app data stored in included sqlite3 db
------------------------------------------------
Usage:
Create virtualenv with python 3.x interpreter
Place project main directory inside and change directory
to "twitterproven"
Install dependencies with pip install -r requirements.txt
--
Optionally (if missing current db file), create database and load initial data with
python twitterprovenweb/manage.py makemigrations
python twitterprovenweb/manage.py migrate
python twitterprovenweb/manage.py loaddata tpw/fixtures/initialdata.dmp
--
Make sure ALLOWED_HOSTS in twitterprovenweb/twitterprovenweb/settings.py is set correctly
Run with: python twitterprovenweb/manage.py runserver
Go to url: 127.0.0.1:8000/tweetcontrol/config
Setup twitter account data (already set to app created by Philip)
Setup postgresql database connection (defaults to host: 127.0.0.1, db: proven, user: proven, no passwd)
------------------------------------------------
Should be good to go:
All pages are served under <host>/tweetcontrol
Visiting <host>/tweetcontrol/list will display errors on red font at the begining of page,
if twitter account or database is not correctly configured.
