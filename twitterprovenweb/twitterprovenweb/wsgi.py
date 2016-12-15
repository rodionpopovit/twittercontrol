"""
WSGI config for twitterprovenweb project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
import threading

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "twitterprovenweb.settings")

from tpw.tweetprov.maincontrol import Proven
p = Proven()
t = threading.Thread(target=p.run, name='PROVEN-BG-TASK')
t.start()

application = get_wsgi_application()
