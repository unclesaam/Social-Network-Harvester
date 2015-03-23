# coding=UTF-8

from tendo import singleton

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from cronharvester import twitterch

import snhlogger
logger = snhlogger.init_logger(__name__, "twitter.log")

class Command(BaseCommand):
    help = 'Search the Twitter\'s API for new content'

    def handle(self, *args, **options):

        me = singleton.SingleInstance(flavor_id="crontw")

        try:
            logger.info("Will run the Twitter harvesters.")
            twitterch.run_twitter_harvester()
        except:
            print "Global failure. exception logged in 'twitter.log'"
            msg = u"Highest exception for the twitter cron. Not good."
            logger.exception(msg)

        logger.info("The harvest has end for the Twitter harvesters."+"     "*200)



        
