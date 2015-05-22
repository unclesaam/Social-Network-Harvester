# coding=UTF-8
from collections import deque
from datetime import datetime
import time

from httplib2 import Http
from urllib import urlencode
import json
import urllib2

from django.db import models
from snh.models.common import *


import snhlogger
logger = snhlogger.init_logger(__name__, "dailymotion.log")

from settings import DEBUGCONTROL
debugging = DEBUGCONTROL['dailymotionmodel']
if DEBUGCONTROL['dailymotionmodel']: 
    print "DEBBUGING ENABLED IN %s"%__name__
    debugLogger = snhlogger.init_custom_logger('debug'+__name__, "debugLogger.log", '(%(filename)-17s) %(message)s')

class DailyMotionHarvester(AbstractHaverster):

    harvester_type = "DailyMotion"

    base = 'https://api.dailymotion.com/json'
    oauth = 'https://api.dailymotion.com/oauth/token'

    key = models.CharField(max_length=255, null=True)
    secret = models.CharField(max_length=255, null=True)
    user = models.CharField(max_length=255, null=True)
    password = models.CharField(max_length=255, null=True)

    access_token = None
    refresh_token = None
    uurl = None

    dmusers_to_harvest = models.ManyToManyField('DMUser', related_name='dmusers_to_harvest')

    last_harvested_user = models.ForeignKey('DMUser',  related_name='last_harvested_user', null=True)
    current_harvested_user = models.ForeignKey('DMUser', related_name='current_harvested_user',  null=True)

    haverst_deque = None

    def get_token(self):
        if not self.access_token:
            values = {'grant_type' : 'password',
                      'client_id' : self.key,
                      'client_secret' : self.secret,
                      'username' : self.user,
                      'password' : self.password,
                      'scope':'write'
                      }

            data = urlencode(values)
            req = urllib2.Request(self.oauth, data)
            response = urllib2.urlopen(req)

            result=json.load(response)
            self.access_token = result['access_token']
            self.refresh_token = result['refresh_token']

            self.uurl='?access_token=' + self.access_token
            
        return self.uurl

    def update_client_stats(self):
        self.save()

    def end_current_harvest(self):
        self.update_client_stats()
        if self.current_harvested_user:
            self.last_harvested_user = self.current_harvested_user
        super(DailyMotionHarvester, self).end_current_harvest()

    def check_error(self, result):
        if result:
            if type(result) == dict:
                if "error" not in result:
                    return result, False
                elif result["error"]["code"] == 500:
                    logger.info("DMError:(%s)-[%s] %s!!!" % (result["error"]["code"],result["error"]["type"], result["error"]["message"]))
                    return None, True
                else:
                    raise Exception("DMError:(%s)-[%s] %s!!!" % (result["error"]["code"],result["error"]["type"], result["error"]["message"]))
            else:
                logger.error("Result is not a dict!!! %s" % result)
                raise Exception("Result is not a dict!!!")
        else:
            raise Exception("Empty result!!!")

    def api_call(self, method, params):
        super(DailyMotionHarvester, self).api_call(method, params)

        retry_count = 0
        retry = True
        ret_val = None
        while retry_count < self.max_retry_on_fail and retry:
            if retry_count > 0:
                logger.info("Retrying last API call... %d/%d" % (retry_count, self.max_retry_on_fail))
            retry_count += 1
            job=json.dumps({"call":"%s %s" % (method, params),"args":None})
            req = urllib2.Request(self.base+self.get_token(), job, {'content-type': 'application/json'})
            response = urllib2.urlopen(req)
            result=json.load(response)
            ret_val, retry = self.check_error(result)

        return ret_val

    def get_last_harvested_user(self):
        return self.last_harvested_user
    
    def get_current_harvested_user(self):
        return self.current_harvested_user

    def get_next_user_to_harvest(self):

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
        self.haverst_deque = deque()
        all_users = self.dmusers_to_harvest.all()

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
        parent_stats = super(DailyMotionHarvester, self).get_stats()
        parent_stats["concrete"] = {}
        return parent_stats
            
class DMUser(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.username

    def related_label(self):
        return u"%s (%s)" % (self.username, self.pmk_id)

    pmk_id =  models.AutoField(primary_key=True)

    fid = models.CharField(max_length=255, null=True)
    username = models.CharField(max_length=255, null=True)
    screenname = models.CharField(max_length=255, null=True)
    gender = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    language = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=255, null=True)
    ftype = models.CharField(max_length=255, null=True)

    url = models.ForeignKey('URL', related_name="dmuser.url", null=True)

    fans = models.ManyToManyField('DMUser', related_name='dmuser.fans')
    friends = models.ManyToManyField('DMUser', related_name='dmuser.friends')
    following = models.ManyToManyField('DMUser', related_name='dmuser.following')

    avatar_small_url = models.ForeignKey('URL', related_name="dmuser.avatar_small_url", null=True)
    avatar_medium_url = models.ForeignKey('URL', related_name="dmuser.avatar_medium_url", null=True)
    avatar_large_url = models.ForeignKey('URL', related_name="dmuser.avatar_large_url", null=True)

    videostar = models.ForeignKey('DMVideo', related_name="dmuser.videostar", null=True)
    views_total = models.IntegerField(null=True)
    videos_total = models.IntegerField(null=True)
    created_time = models.DateTimeField(null=True)

    error_triggered = models.BooleanField()
    updated_time = models.DateTimeField(null=True)

    def update_url_fk(self, self_prop, face_prop, dailymotion_model):
        model_changed = False
        if face_prop in dailymotion_model:
            prop_val = dailymotion_model[face_prop]
            if self_prop is None or self_prop.original_url != prop_val:
                url = None
                try:
                    url = URL.objects.filter(original_url=prop_val)[0]
                except:
                    pass

                if url is None:
                    url = URL(original_url=prop_val)
                    url.save()

                self_prop = url
                model_changed = True
        return model_changed, self_prop

    def update_fan_from_dailymotion(self, fan):
        model_changed = False

        if self.fans.filter(fid__exact=fan["id"]).count() == 0:
            snh_user = None
            try:
                snh_user = DMUser.objects.get(fid__exact=fan["id"])
                snh_user.update_from_dailymotion(fan)
                snh_user.save()

            except:
                pass
            if snh_user is None:
                snh_user = DMUser(
                                    fid=fan["id"],
                                    screenname=fan["screenname"],
                                    )
                snh_user.update_from_dailymotion(fan)
                snh_user.save()

            self.fans.add(snh_user)
            model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.save()

        return model_changed

    def update_friend_from_dailymotion(self, friend):
        model_changed = False

        if self.friends.filter(fid__exact=friend["id"]).count() == 0:
            snh_user = None
            try:
                snh_user = DMUser.objects.get(fid__exact=friend["id"])
                snh_user.update_from_dailymotion(friend)
                snh_user.save()
            except:
                pass
            if snh_user is None:
                snh_user = DMUser(
                                    fid=friend["id"],
                                    screenname=friend["screenname"],
                                    )
                snh_user.update_from_dailymotion(friend)
                snh_user.save()

            self.friends.add(snh_user)
            model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.save()

        return model_changed

    def update_following_from_dailymotion(self, following):
        model_changed = False

        if self.following.filter(fid__exact=following["id"]).count() == 0:
            snh_user = None
            try:
                snh_user = DMUser.objects.get(fid__exact=following["id"])
                snh_user.update_from_dailymotion(following)
                snh_user.save()

            except:
                pass
            if snh_user is None:
                snh_user = DMUser(
                                    fid=following["id"],
                                    screenname=following["screenname"],
                                    )
                snh_user.update_from_dailymotion(following)
                snh_user.save()

            self.following.add(snh_user)
            model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.save()

        return model_changed

    def update_from_dailymotion(self, dm_user):
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"screenname":u"screenname",
                            u"username":u"username",
                            u"gender":u"gender",
                            u"description":u"description",
                            u"language":u"language",
                            u"status":u"status",
                            u"views_total":u"views_total",
                            u"videos_total":u"videos_total",
                            u"ftype":u"type",
                            }

        date_to_check = {"created_time":"created_time"}
        date_to_check = {}

        for prop in props_to_check:
            if props_to_check[prop] in dm_user and unicode(self.__dict__[prop]) != unicode(dm_user[props_to_check[prop]]):
                self.__dict__[prop] = dm_user[props_to_check[prop]]
                #print "prop changed. %s = %s" % (prop, dm_user[props_to_check[prop]])
                model_changed = True

        for prop in date_to_check:
            if date_to_check[prop] in dm_user and self.__dict__[prop] != dm_user[date_to_check[prop]]:
                date_val = datetime.strptime(dm_user[prop],'%m/%d/%Y')
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True

        (changed, self_prop) = self.update_url_fk(self.url, "url", dm_user)
        if changed:
            self.url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.avatar_small_url, "avatar_small_url", dm_user)
        if changed:
            self.avatar_small_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.avatar_medium_url, "avatar_medium_url", dm_user)
        if changed:
            self.avatar_medium_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.avatar_large_url, "avatar_large_url", dm_user)
        if changed:
            self.avatar_large_url = self_prop
            model_changed = True
            
        if model_changed:
            self.model_update_date = datetime.utcnow()
            #print self.pmk_id, self.fid, self, self.__dict__, dm_user
            self.save()

        return model_changed

class DMVideo(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.title

    pmk_id =  models.AutoField(primary_key=True)
    
    user = models.ForeignKey('DMUser',  related_name='dmvideo.user')
    
    fid =  models.CharField(max_length=255, null=True)
    title = models.TextField(null=True)
    tag =  models.TextField(null=True)
    tags = models.TextField(null=True)#models.ManyToManyField('Tag', related_name='dmvideo.tags')
    description = models.TextField(null=True)
    language =  models.CharField(max_length=255, null=True)
    country =  models.CharField(max_length=255, null=True)

    url = models.ForeignKey('URL', related_name="dmvideo.url", null=True)
    tiny_url = models.ForeignKey('URL', related_name="dmvideo.tiny_url", null=True)

    created_time = models.DateTimeField(null=True)
    taken_time = models.DateTimeField(null=True)
    modified_time = models.DateTimeField(null=True)

    status =  models.CharField(max_length=255, null=True)
    encoding_progress = models.IntegerField(null=True)
    ftype = models.CharField(max_length=255, null=True)
    paywall = models.BooleanField()
    rental_duration = models.IntegerField(null=True)

    onair = models.BooleanField()
    mode =  models.CharField(max_length=255, null=True)
    live_publish_url = models.ForeignKey('URL', related_name="dmvideo.live_publish_url", null=True)

    private = models.BooleanField()
    explicit = models.BooleanField()

    published = models.BooleanField()
    duration = models.IntegerField(null=True)
    allow_comments = models.BooleanField()

    thumbnail_url = models.ForeignKey('URL', related_name="dmvideo.thumbnail_url", null=True)
    thumbnail_small_url = models.ForeignKey('URL', related_name="dmvideo.thumbnail_small_url", null=True)
    thumbnail_medium_url = models.ForeignKey('URL', related_name="dmvideo.thumbnail_medium_url", null=True)
    thumbnail_large_url = models.ForeignKey('URL', related_name="dmvideo.thumbnail_large_url", null=True)

    rating = models.IntegerField(null=True)
    ratings_total = models.IntegerField(null=True)

    views_total = models.IntegerField(null=True)
    views_last_hour = models.IntegerField(null=True)
    views_last_day = models.IntegerField(null=True)
    views_last_week = models.IntegerField(null=True)
    views_last_month = models.IntegerField(null=True)

    comments_total = models.IntegerField(null=True)
    bookmarks_total = models.IntegerField(null=True)

    embed_html = models.TextField(null=True)
    embed_url = models.ForeignKey('URL', related_name="dmvideo.embed_url", null=True)
    swf_url = models.ForeignKey('URL', related_name="dmvideo.swf_url", null=True)

    aspect_ratio = models.DecimalField(max_digits=13, decimal_places=12, null=True)
    upc = models.CharField(max_length=255, null=True)
    isrc =  models.CharField(max_length=255, null=True)

    geoblocking = models.TextField(null=True)
    in_3d = models.BooleanField()

    video_file_path = models.TextField(null=True)

    def update_url_fk(self, self_prop, face_prop, dailymotion_model):
        model_changed = False
        if face_prop in dailymotion_model:
            prop_val = dailymotion_model[face_prop]
            if self_prop is None or self_prop.original_url != prop_val:
                url = None
                try:
                    url = URL.objects.filter(original_url=prop_val)[0]
                except:
                    pass

                if url is None:
                    url = URL(original_url=prop_val)
                    url.save()

                self_prop = url
                model_changed = True
        return model_changed, self_prop

    def update_from_dailymotion(self, snh_user, dm_video):
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"title":u"title",
                            u"tag":u"tag",
                            u"tags":u"tags",
                            u"description":u"description",
                            u"language":u"language",
                            u"country":u"country",
                            u"status":u"status",
                            u"encoding_progress":u"encoding_progress",
                            u"ftype":u"type",
                            u"paywall":u"paywall",
                            u"rental_duration":u"rental_duration",
                            u"onair":u"onair",
                            u"mode":u"mode",
                            u"private":u"private",
                            u"explicit":u"explicit",
                            u"published":u"published",
                            u"duration":u"duration",
                            u"allow_comments":u"allow_comments",
                            u"rating":u"rating",
                            u"ratings_total":u"ratings_total",
                            u"views_total":u"views_total",
                            u"views_last_hour":u"views_last_hour",
                            u"views_last_day":u"views_last_day",
                            u"views_last_week":u"views_last_week",
                            u"views_last_month":u"views_last_month",
                            u"comments_total":u"comments_total",
                            u"bookmarks_total":u"bookmarks_total",
                            u"embed_html":u"embed_html",
                            u"aspect_ratio":u"aspect_ratio",
                            u"upc":u"upc",
                            u"isrc":u"isrc",
                            u"geoblocking":u"geoblocking",
                            u"in_3d":u"3d",
                            }

        date_to_check = {
                            "created_time":"created_time",
                            "taken_time":"taken_time",
                            "modified_time":"modified_time",
                            }

        if self.user != snh_user:
            self.user = snh_user
            model_changed = True

        for prop in props_to_check:
            if props_to_check[prop] in dm_video and unicode(self.__dict__[prop]) != unicode(dm_video[props_to_check[prop]]):
                self.__dict__[prop] = dm_video[props_to_check[prop]]
                model_changed = True

        for prop in date_to_check:
            if date_to_check[prop] in dm_video and self.__dict__[prop] != dm_video[date_to_check[prop]]:
                date_val = datetime.fromtimestamp(float(dm_video[prop]))
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True

        (changed, self_prop) = self.update_url_fk(self.url, "url", dm_video)
        if changed:
            self.url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.tiny_url, "tiny_url", dm_video)
        if changed:
            self.tiny_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.live_publish_url, "live_publish_url", dm_video)
        if changed:
            self.live_publish_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.thumbnail_url, "thumbnail_url", dm_video)
        if changed:
            self.thumbnail_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.thumbnail_small_url, "thumbnail_small_url", dm_video)
        if changed:
            self.thumbnail_small_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.thumbnail_medium_url, "thumbnail_medium_url", dm_video)
        if changed:
            self.thumbnail_medium_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.thumbnail_large_url, "thumbnail_large_url", dm_video)
        if changed:
            self.thumbnail_large_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.embed_url, "embed_url", dm_video)
        if changed:
            self.embed_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.swf_url, "swf_url", dm_video)
        if changed:
            self.swf_url = self_prop
            model_changed = True
            
        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.save()

        return model_changed

class DMComment(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.title

    pmk_id =  models.AutoField(primary_key=True)

    fid =  models.CharField(max_length=255, null=True)

    user = models.ForeignKey('DMUser',  related_name='dmcomment.user', null=True)
    video = models.ForeignKey('DMVideo',  related_name='dmcomment.video')

    message = models.TextField(null=True)
    language =  models.CharField(max_length=255, null=True)
    created_time = models.DateTimeField(null=True)
    locked = models.BooleanField()

    def update_from_dailymotion(self, snh_video, snh_user, dm_comment):
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"message":u"message",
                            u"language":u"language",
                            u"locked":u"locked",
                            }

        date_to_check = {
                            "created_time":"created_time",
                            }

        if self.video != snh_video:
            self.video = snh_video
            model_changed = True

        if self.user != snh_user:
            self.user = snh_user
            model_changed = True

        for prop in props_to_check:
            if props_to_check[prop] in dm_comment and unicode(self.__dict__[prop]) != unicode(dm_comment[props_to_check[prop]]):
                self.__dict__[prop] = dm_comment[props_to_check[prop]]
                model_changed = True

        for prop in date_to_check:
            if date_to_check[prop] in dm_comment and self.__dict__[prop] != dm_comment[date_to_check[prop]]:
                date_val = datetime.fromtimestamp(float(dm_comment[prop]))
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.save()

        return model_changed









