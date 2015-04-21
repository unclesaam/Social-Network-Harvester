# coding=UTF-8
from collections import deque
from django.db import models
from datetime import datetime
import time

import twitter as pytw
from twython import Twython

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from snh.models.common import *

import snhlogger
import re


#########################################################
debugging = 0
if debugging: 
    print "DEBBUGING ENABLED IN %s"%__name__
    debugLogger = snhlogger.init_custom_logger('debug'+__name__, "debugLogger.log", '%(message)s')
#########################################################

def gie(d, k):
    return d[k] if k in d else None 

class TwitterHarvester(AbstractHaverster):

    harvester_type = "Twitter"

    client = None
    tt_client = None

    consumer_key = models.CharField(max_length=255,null=True)
    consumer_secret = models.CharField(max_length=255,null=True)
    access_token_key = models.CharField(max_length=255,null=True)
    access_token_secret = models.CharField(max_length=255,null=True)

    remaining_hits = models.IntegerField(null=True)
    reset_time_in_seconds = models.IntegerField(null=True)
    hourly_limit = models.IntegerField(null=True)
    reset_time = models.DateTimeField(null=True)

    twusers_to_harvest = models.ManyToManyField('TWUser', related_name='twusers_to_harvest')
    twsearch_to_harvest = models.ManyToManyField('TWSearch', related_name='twitterharvester.twsearch_to_harvest')

    last_harvested_user = models.ForeignKey('TWUser',  related_name='last_harvested_user', null=True)
    current_harvested_user = models.ForeignKey('TWUser', related_name='current_harvested_user',  null=True)

    haverst_deque = None

    def get_client(self):
        if debugging: debugLogger.info( "<TWHarvester>%s::get_client()"%self.harvester_name)

        if not self.client:
            self.client = pytw.Api(consumer_key=self.consumer_key,
                                        consumer_secret=self.consumer_secret,
                                        access_token_key=self.access_token_key,
                                        access_token_secret=self.access_token_secret,
                                     )
        return self.client

    def get_tt_client(self):
        if debugging: debugLogger.info( "<TWHarvester>%s::get_tt_client()"%self.harvester_name)

        if not self.tt_client:
            self.tt_client = Twython(self.consumer_key,self.consumer_secret,self.access_token_key,self.access_token_secret)

        return self.tt_client

    """
    update the remaining searches the instance is allowed to do before annoying Twitter
    """
    def update_client_stats(self):
        if debugging: debugLogger.info( "<TWHarvester>%s::update_client_stats()"%self.harvester_name)

        c = self.get_client()
        rate = c.GetRateLimitStatus("search")["resources"]["search"]["/search/tweets"]

        self.remaining_hits = rate["remaining"]
        self.reset_time_in_seconds = rate["reset"]
        self.hourly_limit = rate["limit"] 
        self.reset_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(rate["reset"]))
        self.save()

    def end_current_harvest(self):
        if debugging: debugLogger.info( "<TWHarvester>%s::end_current_harvest()"%self.harvester_name)
        self.update_client_stats()
        if self.current_harvested_user:
            self.last_harvested_user = self.current_harvested_user
        super(TwitterHarvester, self).end_current_harvest()

    def api_call(self, method, params):
        if debugging: debugLogger.info( "<TWHarvester>%s::api_call(method: %s, params: %s"%(self.harvester_name, method, params))
        super(TwitterHarvester, self).api_call(method, params)
        c = self.get_client()   
        metp = getattr(c, method)
        return metp(**params)

    def get_last_harvested_user(self):
        return self.last_harvested_user
    
    def get_current_harvested_user(self):
        return self.current_harvested_user

    def get_next_user_to_harvest(self):
        if debugging: debugLogger.info( "<TWHarvester>%s::get_next_user_to_harvest()"%self.harvester_name)

        if self.current_harvested_user:
            self.last_harvested_user = self.current_harvested_user

        if self.haverst_deque is None:
            self.build_harvester_sequence()

        try:
            self.current_harvested_user = self.haverst_deque.pop()
        except IndexError:
            self.current_harvested_user = None

        self.update_client_stats()
        return self.current_harvested_user

    def build_harvester_sequence(self):
        if debugging: debugLogger.info( "<TWHarvester>%s::build_harvester_sequence()"%self.harvester_name)
        self.haverst_deque = deque()
        all_users = self.twusers_to_harvest.all()

        if self.last_harvested_user:
            count = 0
            for user in all_users:
                if user == self.last_harvested_user:
                    break
                count = count + 1
            retry_last_on_fail = 1 if self.retry_user_after_abortion and self.last_user_harvest_was_aborted else 0
            self.haverst_deque.extend(all_users[count+retry_last_on_fail:])
            self.haverst_deque.extend(all_users[:count+retry_last_on_fail])
        else:
            self.haverst_deque.extend(all_users)

    def get_stats(self):
        if debugging: debugLogger.info( "<TWHarvester>%s::get_stats()"%self.harvester_name)
        parent_stats = super(TwitterHarvester, self).get_stats()
        parent_stats["concrete"] = {
                                    "remaining_hits":self.remaining_hits,
                                    "reset_time_in_seconds":self.reset_time_in_seconds,
                                    "hourly_limit":self.hourly_limit,
                                    "reset_time":self.reset_time,
                                    "last_harvested_user":unicode(self.last_harvested_user),
                                    "current_harvested_user":unicode(self.current_harvested_user),
                                    }
        return parent_stats

            
class TWSearch(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.term

    def related_label(self):
        return u"%s (%s)" % (self.term, self.pmk_id)


    pmk_id =  models.AutoField(primary_key=True)
    term = models.TextField(null=True)
    status_list = models.ManyToManyField('TWStatus', related_name='twsearch.status_list')
    latest_status_harvested = models.ForeignKey('TWStatus',  related_name='TWSearch.latest_status_harvested', null=True)

class TWUser(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.screen_name.encode('ascii', 'ignore')

    def related_label(self):
        return u"%s (%s)" % (self.screen_name, self.pmk_id)

    pmk_id =  models.AutoField(primary_key=True)

    fid = models.BigIntegerField(null=True, unique=True)
    name = models.CharField(max_length=255, null=True)
    screen_name = models.CharField(max_length=255, null=True, unique=True)
    lang = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    url = models.ForeignKey('URL', related_name="twuser.url", null=True)

    location = models.TextField(null=True)
    time_zone = models.TextField(null=True)
    utc_offset = models.IntegerField(null=True)

    protected = models.BooleanField()

    favourites_count = models.IntegerField(null=True)
    followers_count = models.IntegerField(null=True)
    friends_count = models.IntegerField(null=True)
    statuses_count = models.IntegerField(null=True)
    listed_count = models.IntegerField(null=True)

    created_at = models.DateTimeField(null=True)

    profile_background_color = models.CharField(max_length=255, null=True)
    profile_background_tile = models.BooleanField()
    profile_background_image_url = models.ForeignKey('URL', related_name="twuser.profile_background_image_url", null=True)
    profile_image_url = models.ForeignKey('URL', related_name="twuser.profile_image_url", null=True)
    profile_link_color = models.CharField(max_length=255, null=True)
    profile_sidebar_fill_color = models.CharField(max_length=255, null=True)
    profile_text_color = models.CharField(max_length=255, null=True)

    model_update_date = models.DateTimeField(null=True)
    error_triggered = models.BooleanField()
    error_on_update = models.BooleanField()

    was_aborted = models.BooleanField()
    last_harvested_status = models.ForeignKey('TWStatus',  related_name='TWStatus.last_harvested_status', null=True)

    def update_from_rawtwitter(self, twitter_model, twython=False):
        if debugging: debugLogger.info( "<TWUser>%s::update_from_rawtwitter(twitter_model: %s)"%(self.screen_name, type(twitter_model)))

        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"name":u"name",
                            u"screen_name":u"screen_name",
                            u"lang":u"lang",
                            u"description":u"description",
                            u"location":u"location",
                            u"time_zone":u"time_zone",
                            u"utc_offset":u"utc_offset",
                            u"protected":u"protected",
                            u"favourites_count":u"favourites_count",
                            u"followers_count":u"followers_count",
                            u"friends_count":u"friends_count",
                            u"statuses_count":u"statuses_count",
                            u"listed_count":u"listed_count",
                            u"profile_background_color":u"profile_background_color",
                            u"profile_background_tile":u"profile_background_tile",
                            u"profile_link_color":u"profile_link_color",
                            u"profile_sidebar_fill_color":u"profile_sidebar_fill_color",
                            u"profile_text_color":u"profile_text_color",
                            }

        date_to_check = ["created_at"]

        for prop in props_to_check:
            prop_name = props_to_check[prop]
            if prop_name in twitter_model:
                tw_val = twitter_model[prop_name]
                if self.__dict__[prop] != tw_val:
                    self.__dict__[prop] = tw_val
                    model_changed = True

        for prop in date_to_check:
            if prop in twitter_model:
                tw_prop_val = twitter_model[prop]
                format = '%a, %d %b %Y %H:%M:%S +0000'              
                if twython:
                    format = '%a %b %d %H:%M:%S +0000 %Y'
                date_val = datetime.strptime(tw_prop_val,format)
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True


        if "url" in twitter_model:
            tw_prop_val = twitter_model["url"]
            if self.url is None or self.url.original_url != tw_prop_val:
                tw_url = URL()
                tw_url.original_url = tw_prop_val
                tw_url.save()
                self.url = tw_url
                model_changed = True

        if "profile_image_url" in twitter_model:
            tw_prop_val = twitter_model["profile_image_url"]
            if self.profile_image_url is None or self.profile_image_url.original_url != tw_prop_val:
                tw_url = URL()
                tw_url.original_url = tw_prop_val
                tw_url.save()
                self.profile_image_url = tw_url
                model_changed = True

        if "profile_background_image_url" in twitter_model:
            tw_prop_val = twitter_model["profile_background_image_url"]
            if self.profile_background_image_url is None or self.profile_background_image_url.original_url != tw_prop_val:
                tw_url = URL()
                tw_url.original_url = tw_prop_val
                tw_url.save()
                self.profile_image_url = tw_url
                model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.error_on_update = False
            self.save()

    def update_from_twitter(self, twitter_model):
        if debugging: debugLogger.info( "<TWUser>%s::update_from_twitter(twitter_model: %s)"%(self.screen_name, type(twitter_model)))

        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"name":u"name",
                            u"screen_name":u"screen_name",
                            u"lang":u"lang",
                            u"description":u"description",
                            u"location":u"location",
                            u"time_zone":u"time_zone",
                            u"utc_offset":u"utc_offset",
                            u"protected":u"protected",
                            u"favourites_count":u"favourites_count",
                            u"followers_count":u"followers_count",
                            u"friends_count":u"friends_count",
                            u"statuses_count":u"statuses_count",
                            u"listed_count":u"listed_count",
                            u"profile_background_color":u"profile_background_color",
                            u"profile_background_tile":u"profile_background_tile",
                            u"profile_link_color":u"profile_link_color",
                            u"profile_sidebar_fill_color":u"profile_sidebar_fill_color",
                            u"profile_text_color":u"profile_text_color",
                            }

        date_to_check = ["created_at"]

        for prop in props_to_check:
            prop_name = "_"+props_to_check[prop]
            if prop_name in twitter_model.__dict__:
                tw_val = twitter_model.__dict__[prop_name]
                if self.__dict__[prop] != tw_val:
                    self.__dict__[prop] = tw_val
                    model_changed = True

        for prop in date_to_check:
            prop_name = "_"+prop
            if prop_name in twitter_model.__dict__:
                tw_prop_val = twitter_model.__dict__[prop_name]
                date_val = datetime.strptime(tw_prop_val,'%a %b %d %H:%M:%S +0000 %Y')
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True


        if "_url" in twitter_model.__dict__:
            tw_prop_val = twitter_model.__dict__["_url"]
            if self.url is None or self.url.original_url != tw_prop_val:
                tw_url = URL()
                tw_url.original_url = tw_prop_val
                tw_url.save()
                self.url = tw_url
                model_changed = True

        if "_profile_image_url" in twitter_model.__dict__:
            tw_prop_val = twitter_model.__dict__["_profile_image_url"]
            if self.profile_image_url is None or self.profile_image_url.original_url != tw_prop_val:
                tw_url = URL()
                tw_url.original_url = tw_prop_val
                tw_url.save()
                self.profile_image_url = tw_url
                model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.error_on_update = False
            self.save()

    def get_latest_status(self):
        if debugging: print "%s::get_latest_status"%(self.screen_name)

        latest_status = None
        statuses = TWStatus.objects.filter(user=self).order_by("created_at")
        for latest_status in statuses: break
        return latest_status
        







class TWStatus(models.Model):

    class Meta:
        app_label = "snh"
        verbose_name_plural = "Tw statuses"
        verbose_name = "Tw status"

    def __unicode__(self):
        if self.text:
            if len(self.text) > 60:
                return "%s..."%self.text[:60]
            else:
                return self.text
        else:
            return "status from %s"%self.user

    pmk_id =  models.AutoField(primary_key=True)

    user = models.ForeignKey('TWUser', related_name='postedStatuses')

    fid = models.BigIntegerField(null=True, unique=True)
    created_at = models.DateTimeField(null=True)
    favorited = models.BooleanField()
    retweet_count = models.IntegerField(null=True)
    retweeted = models.BooleanField()
    source = models.TextField(null=True)
    text = models.TextField(null=True)
    truncated = models.BooleanField()

    text_urls = models.ManyToManyField('URL', related_name='twstatus_text_urls')
    hash_tags = models.ManyToManyField('Tag', related_name='twstatus_tag')
    user_mentions = models.ManyToManyField('TWUser', related_name='mentionedInStatuses')

    model_update_date = models.DateTimeField(null=True)
    error_on_update = models.BooleanField()

    """
    digest_source
    return a list of self, the name of the source app and its url
    """
    def digest_source(self):
        if self.source:
            source_title = re.search(r'>(?P<title>.*)</a>', self.source).group('title')
            source_href = re.search(r'href="(?P<href>.*)" rel=', self.source).group('href')
            return (self, source_title, source_href)
        return (self, None, None)

    def get_existing_user(self, param):
        if debugging: debugLogger.info( "<TWStatus>'%s'::get_existing_user(param: %s)"%(self, param))

        user = None
        try:
            user = TWUser.objects.get(**param)
        except MultipleObjectsReturned:
            user = TWUser.objects.filter(**param)[0]
        except ObjectDoesNotExist:
            pass
        return user

    def update_from_rawtwitter(self, twitter_model, user, twython=False):
        if debugging: debugLogger.info( "<TWStatus>'%s'::update_from_rawtwitter(twitter_model: %s, user: %s)"%(self, type(twitter_model), user))

        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"favorited":u"favorited",
                            u"retweet_count":u"retweet_count",
                            u"retweeted":u"retweeted",
                            u"source":u"source",
                            u"text":u"text",
                            u"truncated":u"truncated",
                            }

        date_to_check = ["created_at"]

        self.user = user

        for prop in props_to_check:
            prop_name = props_to_check[prop]
            if hasattr(twitter_model, prop_name):
                tw_prop_val = getattr(twitter_model, prop_name)
                if self.__dict__[prop] != tw_prop_val:
                    self.__dict__[prop] = tw_prop_val
                    model_changed = True

        for prop in date_to_check:
            if hasattr(twitter_model, prop):
                tw_prop_val = getattr(twitter_model, prop)
                format = '%a %b %d %H:%M:%S +0000 %Y'              
                if twython:
                    format = '%a %b %d %H:%M:%S +0000 %Y'
                date_val = datetime.strptime(tw_prop_val,format)
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True


        if hasattr(twitter_model, "entities"):
            entities = getattr(twitter_model, "entities")
            if "hashtags" in entities:
                tw_prop_val = entities["hashtags"]
                for twtag in tw_prop_val:
                    tag = None
                    try:
                        tag = Tag.objects.get(text__exact=twtag["text"])
                    except:
                        pass

                    if tag is None:
                        tag = Tag(text=twtag["text"])
                        tag.save()
                        self.hash_tags.add(tag)
                        model_changed = True
                    else:
                        
                        if tag not in self.hash_tags.all():
                            self.hash_tags.add(tag)
                            model_changed = True

            if hasattr(entities, "urls"):
                tw_prop_val = getattr(entities, "urls")
                for twurl in tw_prop_val:
                    url = None
                    try:
                        url = URL.objects.get(original_url__exact=twurl.url)
                    except:
                        pass

                    if url is None:
                        url = URL(original_url=twurl.url)
                        url.save()
                        self.text_urls.add(url)
                        model_changed = True
                    else:
                        
                        if url not in self.text_urls.all():
                            self.text_urls.add(url)
                            model_changed = True                        

            if hasattr(entities, "user_mentions"):
                tw_prop_val = getattr(entities, "user_mentions")
                for tw_mention in tw_prop_val:
                    usermention = None
                    try:
                        usermention = self.get_existing_user({"fid__exact":tw_mention.id})
                        if not usermention:
                            usermention = self.get_existing_user({"screen_name__exact":tw_mention.screen_name})
                        if not usermention:
                            usermention = TWUser(
                                            fid=tw_mention.id,
                                            screen_name=tw_mention.screen_name,
                                         )
                        usermention.update_from_rawtwitter(tw_mention,twython)
                        usermention.save()
                    except:
                        pass

                    if usermention is None:
                        usermention = TWUser(
                                        fid=tw_mention.id,
                                     )
                        usermention.update_from_rawtwitter(tw_mention, twython)
                        usermention.save()
                        self.user_mentions.add(usermention)
                        model_changed = True
                    else:
                        if usermention not in self.user_mentions.all():
                            self.user_mentions.add(usermention)
                            model_changed = True    

        if model_changed:
            text = re.sub(r'(\\\\x..)', '', self.text) #removing emojis from texts
            self.text = self.text.encode('ascii', 'ignore')
            self.model_update_date = datetime.utcnow()
            self.error_on_update = False
            try:
                self.save()
            except:
                print self.text.encode('ascii', 'ignore')


    def update_from_twitter(self, twitter_model, user):
        if debugging: debugLogger.info( "<TWStatus>'%s'::update_from_twitter(twitter_model: %s, user: %s)"%(self, type(twitter_model), user))
        
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"favorited":u"favorited",
                            u"retweet_count":u"retweet_count",
                            u"retweeted":u"retweeted",
                            u"source":u"source",
                            u"text":u"text",
                            u"truncated":u"truncated",
                            }

        date_to_check = ["created_at"]

        self.user = user

        for prop in props_to_check:
            prop_name = "_"+props_to_check[prop]
            if prop_name in twitter_model.__dict__:
                tw_prop_val = twitter_model.__dict__[prop_name]
                if self.__dict__[prop] != tw_prop_val:
                    self.__dict__[prop] = tw_prop_val
                    model_changed = True

        for prop in date_to_check:
            prop_name = "_"+prop
            if prop_name in twitter_model.__dict__:
                tw_prop_val = twitter_model.__dict__[prop_name]
                date_val = datetime.strptime(tw_prop_val,'%a %b %d %H:%M:%S +0000 %Y')
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True

        if "hashtags" in twitter_model.__dict__:
            tw_prop_val = twitter_model.__dict__["hashtags"]
            for twtag in tw_prop_val:
                tag = None
                try:
                    tag = Tag.objects.filter(text=twtag.text)[0]
                except:
                    pass

                if tag is None:
                    tag = Tag(text=twtag.text)
                    tag.save()
                    self.hash_tags.add(tag)
                    model_changed = True
                else:
                    
                    if tag not in self.hash_tags.all():
                        self.hash_tags.add(tag)
                        model_changed = True

        if "urls" in twitter_model.__dict__:
            tw_prop_val = twitter_model.__dict__["urls"]
            for twurl in tw_prop_val:
                url = None
                try:
                    url = URL.objects.filter(original_url=twurl.url)[0]
                except:
                    pass

                if url is None:
                    url = URL(original_url=twurl.url)
                    url.save()
                    self.text_urls.add(url)
                    model_changed = True
                else:
                    
                    if url not in self.text_urls.all():
                        self.text_urls.add(url)
                        model_changed = True                        

        if "user_mentions" in twitter_model.__dict__:
            tw_prop_val = twitter_model.__dict__["user_mentions"]
            for tw_mention in tw_prop_val:
                usermention = None
                try:

                    usermention = self.get_existing_user({"fid__exact":tw_mention.id})
                    if not usermention:
                        usermention = self.get_existing_user({"screen_name__exact":tw_mention.screen_name})
                    if not usermention:
                        usermention = TWUser(
                                        fid=tw_mention.screen_name.id,
                                        screen_name=tw_mention.screen_name,
                                     )
                except:
                    pass

                if usermention and usermention not in self.user_mentions.all():
                    self.user_mentions.add(usermention)
                    model_changed = True

        if model_changed:
            text = re.sub(r'(\\\\x..)', '', self.text) #removing emojis from texts
            self.text = self.text.encode('ascii', 'ignore')
            self.model_update_date = datetime.utcnow()
            self.error_on_update = False
            self.save()


