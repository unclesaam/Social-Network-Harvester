from tendo import singleton

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from cronharvester import facebookch, youtubech, twitterch

import snhlogger
logger = snhlogger.init_logger(__name__, "ElasticSearch.log")


class Command(BaseCommand):
    #args = '<poll_id poll_id ...>'
    #help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):

        me = singleton.SingleInstance(flavor_id="cronES")

        try:
            logger.info("Will archive data into ElasticSearch")
            twitterch.esArchive()
            #facebookch.esArchive()
            #youtubech.esArchive()
        except:
            msg = u"Highest exception for the ElasticSearch cron. Not good."
            logger.exception(msg)

        logger.info("The archiving into the ElasticSearch has ended.")


