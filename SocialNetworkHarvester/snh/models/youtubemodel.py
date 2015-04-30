# coding=UTF-8
from collections import deque
from datetime import datetime
import time

import gdata.youtube
import gdata.youtube.service

from django.db import models
from snh.models.common import *
import snhlogger
#########################################################
debugging = 1
if debugging: 
    print "DEBBUGING ENABLED IN %s"%__name__
    debugLogger = snhlogger.init_custom_logger('debug'+__name__, "debugLogger.log", '(%(filename)-15s) %(message)s')
    debugLogger.info("            "*100)
#########################################################

class YoutubeHarvester(AbstractHaverster):

    harvester_type = "Youtube"

    ytusers_to_harvest = models.ManyToManyField('YTUser', related_name='ytusers_to_harvest')

    last_harvested_user = models.ForeignKey('YTUser',  related_name='last_harvested_user', null=True)
    current_harvested_user = models.ForeignKey('YTUser', related_name='current_harvested_user',  null=True)

    dev_key = models.TextField(null=True)

    client = None

    haverst_deque = None

    def update_client_stats(self):
        self.save()

    def end_current_harvest(self):
        self.update_client_stats()
        if self.current_harvested_user:
            self.last_harvested_user = self.current_harvested_user
        super(YoutubeHarvester, self).end_current_harvest()

    def api_call(self, method, params):
        if self.client is None:
            self.client = gdata.youtube.service.YouTubeService()
            self.client.developer_key = self.dev_key
            #print self.dev_key         
        super(YoutubeHarvester, self).api_call(method, params)
        time.sleep(0.7)
        metp = getattr(self.client, method)
        ret = metp(**params)
        return ret

    def get_last_harvested_user(self):
        return self.last_harvested_user
    
    def get_current_harvested_user(self):
        return self.current_harvested_user

    def get_next_user_to_harvest(self):
        if debugging: debugLogger.info("%s::get_next_user_to_harvest()", self)
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
        if debugging: debugLogger.info("%s::build_harvester_sequence()", self)
        self.haverst_deque = deque()
        all_users = self.ytusers_to_harvest.all()

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
        if debugging: debugLogger.info("%s::get_stats()", self)
        parent_stats = super(YoutubeHarvester, self).get_stats()
        parent_stats["concrete"] = {}
        return parent_stats
            
class YTUser(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.title if self.title else self.username or u'Unamed User'

    def related_label(self):
        return u"%s (%s)" % (self.username, self.pmk_id)

    pmk_id =  models.AutoField(primary_key=True)

    fid = models.CharField(max_length=255, null=True)

    uri = models.ForeignKey('URL', related_name="ytuser.uri", null=True)
    age = models.IntegerField(null=True)
    gender = models.CharField(max_length=255, null=True)
    location = models.CharField(max_length=255, null=True)

    title = models.CharField(max_length=255, null=True)
    username = models.CharField(max_length=255, null=True)
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    relationship = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)

    link = models.ManyToManyField('URL', related_name="ytuser.link")
    
    company = models.CharField(max_length=255, null=True)
    occupation = models.TextField(null=True)
    school = models.CharField(max_length=255, null=True)
    hobbies = models.TextField(null=True)
    movies = models.TextField(null=True)
    music = models.TextField(null=True)
    books = models.TextField(null=True)
    hometown = models.CharField(max_length=255, null=True)

    error_triggered = models.BooleanField()
    updated_time = models.DateTimeField(null=True)

    last_web_access = models.DateTimeField(null=True)
    subscriber_count = models.IntegerField(null=True)
    video_watch_count = models.IntegerField(null=True)
    view_count = models.IntegerField(null=True)

    def update_from_youtube(self, yt_user): #User
        if debugging: debugLogger.info("<'%s'>::update_from_youtube()", self)
        model_changed = False
        text_to_check = {
                            u"gender":u"gender",
                            u"location":u"location",
                            u"username":u"username",
                            u"first_name":u"first_name",
                            u"last_name":u"last_name",
                            u"relationship":u"relationship",
                            u"description":u"content",
                            u"company":u"company",
                            u"occupation":u"occupation",
                            u"school":u"school",
                            u"hobbies":u"hobbies",
                            u"music":u"music",
                            u"books":u"books",
                            u"hometown":u"hometown",
                            }

        split_uri = yt_user.id.text.split("/")
        fid = split_uri[len(split_uri)-1]

        if self.fid != fid:
            self.fid = fid
            model_changed = True

        if yt_user.age and \
                yt_user.age.text and \
                self.age != int(yt_user.age.text):
            self.age = int(yt_user.age.text)
            #if debugging: debugLogger.info("    age change %d" % self.age )
            model_changed = True

        yt_last_web_access = yt_user.statistics.last_web_access
        date_val = datetime.strptime(yt_last_web_access,'%Y-%m-%dT%H:%M:%S.000Z')
        if self.last_web_access != date_val:
            self.last_web_access = date_val
            model_changed = True

        if yt_user.statistics and \
                yt_user.statistics.subscriber_count and \
                self.subscriber_count != int(yt_user.statistics.subscriber_count):
            self.subscriber_count = int(yt_user.statistics.subscriber_count)
            #if debugging: debugLogger.info("    subscriber_count change %d" % self.subscriber_count)
            model_changed = True

        if yt_user.statistics and \
                yt_user.statistics.video_watch_count and \
                self.video_watch_count != int(yt_user.statistics.video_watch_count):
            self.video_watch_count = int(yt_user.statistics.video_watch_count)
            #if debugging: debugLogger.info("    video_watch_count change %d" % self.video_watch_count)
            model_changed = True

        if yt_user.statistics and \
                yt_user.statistics.view_count and \
                self.view_count != int(yt_user.statistics.view_count):
            self.view_count = int(yt_user.statistics.view_count)
            #if debugging: debugLogger.info("    view_count change %d" % self.view_count )
            model_changed = True

        for prop in text_to_check:
            if text_to_check[prop] in yt_user.__dict__ and \
                    yt_user.__dict__[text_to_check[prop]] and \
                    yt_user.__dict__[text_to_check[prop]].text and \
                    self.__dict__[prop] != unicode(yt_user.__dict__[text_to_check[prop]].text, 'UTF-8'):

                self.__dict__[prop] = unicode(yt_user.__dict__[text_to_check[prop]].text, 'UTF-8') 
                #if debugging: debugLogger.info("    prop changed. %s = %s" % (prop, self.__dict__[prop]) )
                model_changed = True
            
        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.save()

        return model_changed

class YTVideo(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.title[:20] if self.title else 'Untitled video'

    pmk_id =  models.AutoField(primary_key=True)
    
    user = models.ForeignKey('YTUser',  related_name='ytvideo.user')
    fid =  models.CharField(max_length=255, null=True)
    url = models.ForeignKey('URL', related_name="ytvideo.url", null=True)
    player_url = models.ForeignKey('URL', related_name="ytvideo.player_url", null=True)
    swf_url = models.ForeignKey('URL', related_name="ytvideo.swf_url", null=True)
    title = models.TextField(null=True)

    published = models.DateTimeField(null=True)
    updated = models.DateTimeField(null=True)
    recorded = models.DateTimeField(null=True)

    description = models.TextField(null=True)
    category =  models.CharField(max_length=255, null=True)
    #tags = Many2Many
    favorite_count = models.IntegerField(null=True)
    view_count = models.IntegerField(null=True)
    duration = models.IntegerField(null=True)

    video_file_path = models.TextField(null=True)

    def update_from_youtube(self, snh_user, yt_video): #Video
        if debugging: debugLogger.info("<'%s'>::update_from_youtube()", self)
        model_changed = False
        text_to_check = {
                            u"title":u"title",
                            u"description":u"description",
                            }
        split_uri = yt_video.id.text.split("/")
        fid = split_uri[len(split_uri)-1]

        if self.fid != fid:
            self.fid = fid
            model_changed = True

        if self.url is None or self.url.original_url != yt_video.id.text:
            url = None
            try:
                url = URL.objects.filter(original_url=yt_video.id.text)[0]
            except:
                pass

            if url is None:
                url = URL(original_url=yt_video.id.text)
                url.save()
            self.url = url
            model_changed = True

        if self.player_url is None or self.player_url.original_url != yt_video.media.player.url:
            url = None
            try:
                url = URL.objects.filter(original_url=yt_video.media.player.url)[0]
            except:
                pass

            if url is None:
                url = URL(original_url=yt_video.media.player.url)
                url.save()
            self.player_url = url
            model_changed = True

        if self.swf_url is None or self.swf_url.original_url != yt_video.GetSwfUrl():
            url = None
            try:
                url = URL.objects.filter(original_url=yt_video.GetSwfUrl())[0]
            except:
                pass

            if url is None:
                url = URL(original_url=yt_video.GetSwfUrl())
                url.save()
            self.swf_url = url
            model_changed = True

        for prop in text_to_check:
            if text_to_check[prop] in yt_video.media.__dict__ and \
                    yt_video.media.__dict__[text_to_check[prop]] and \
                    yt_video.media.__dict__[text_to_check[prop]].text and \
                    self.__dict__[prop] != unicode(yt_video.media.__dict__[text_to_check[prop]].text, 'UTF-8'):

                self.__dict__[prop] = unicode(yt_video.media.__dict__[text_to_check[prop]].text, 'UTF-8')
                #print "prop changed. %s = %s" % (prop, self.__dict__[prop]) 
                model_changed = True

        yt_published = yt_video.published.text
        date_val = datetime.strptime(yt_published,'%Y-%m-%dT%H:%M:%S.000Z')
        if self.published != date_val:
            self.published = date_val
            model_changed = True

        yt_updated = yt_video.updated.text
        date_val = datetime.strptime(yt_updated,'%Y-%m-%dT%H:%M:%S.000Z')
        if self.updated != date_val:
            self.updated = date_val
            model_changed = True

        if yt_video.recorded:
            yt_recorded = yt_video.recorded.text
            date_val = datetime.strptime(yt_recorded,'%Y-%m-%d')
            if self.recorded != date_val:
                self.recorded = date_val
                model_changed = True

        if yt_video.statistics and \
                yt_video.statistics.view_count and \
                self.view_count != int(yt_video.statistics.view_count):
            self.view_count = int(yt_video.statistics.view_count)
            #print "view_count change %d" % self.view_count 
            model_changed = True

        if yt_video.statistics and \
                yt_video.statistics.favorite_count and \
                self.favorite_count != int(yt_video.statistics.favorite_count):
            self.favorite_count = int(yt_video.statistics.favorite_count)
            #print "favorite_count change %d" % self.favorite_count 
            model_changed = True

        if yt_video.media.duration and \
                yt_video.media.duration.seconds and \
                self.duration != int(yt_video.media.duration.seconds):
            self.duration = int(yt_video.media.duration.seconds)
            #print "duration change %d" % self.duration 
            model_changed = True
        
        if model_changed:
            self.model_update_date = datetime.utcnow()
            #print self.pmk_id, self.fid, self, self.__dict__, yt_video
            self.save()

        return model_changed

class YTComment(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.message[:20] if self.message else u'Empty message'

    pmk_id =  models.AutoField(primary_key=True)

    fid =  models.CharField(max_length=255, null=True)

    user = models.ForeignKey('YTUser',  related_name='ytcomment.user', null=True)
    video = models.ForeignKey('YTVideo',  related_name='ytcomment.video')
    message = models.TextField(null=True)

    published = models.DateTimeField(null=True)
    updated = models.DateTimeField(null=True)

    def update_from_youtube(self, snh_video, snh_user, yt_comment): #Comment
        if debugging: debugLogger.info("<'%s'>::update_from_youtube()", self)
        model_changed = False
        text_to_check = {
                            u"message":u"message",
                            }

        date_to_check = {
                            #"created_time":"created_time",
                            }

        split_uri = yt_comment.id.text.split("/")
        fid = split_uri[len(split_uri)-1]

        if self.fid != fid:
            self.fid = fid
            model_changed = True


        if self.video != snh_video:
            self.video = snh_video
            model_changed = True

        if self.user != snh_user:
            self.user = snh_user
            model_changed = True

        yt_published = yt_comment.published.text
        date_val = datetime.strptime(yt_published,'%Y-%m-%dT%H:%M:%S.000Z')
        if self.published != date_val:
            self.published = date_val
            model_changed = True

        yt_updated = yt_comment.updated.text
        date_val = datetime.strptime(yt_updated,'%Y-%m-%dT%H:%M:%S.000Z')
        if self.updated != date_val:
            self.updated = date_val
            model_changed = True


        content = unicode(yt_comment.content.text, 'UTF-8')
        if self.message != content:
            self.message = content
            model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.save()

        return model_changed









