from __future__ import unicode_literals

from django.apps import AppConfig


class IcsConfig(AppConfig):
    name = 'ics'

    def ready(self):
    	print("in the ready fn")
        import ics.signals  # noqa