# coding=UTF-8
from collections import deque
from datetime import datetime
import time
import re
from apiclient.errors import HttpError

import gdata.youtube
import gdata.youtube.service

from django.db import models
from snh.models.common import *
import snhlogger


from settings import DEBUGCONTROL, dLogger, DEFAULT_API_APPS
debugging = DEBUGCONTROL['youtubemodel']
if debugging: print "DEBBUGING ENABLED IN %s"%__name__

class YoutubeHarvester(AbstractHaverster):

    harvester_type = "Youtube"
    ytusers_to_harvest = models.ManyToManyField('YTUser', related_name='ytusers_to_harvest')
    last_harvested_user = models.ForeignKey('YTUser',  related_name='last_harvested_user', null=True)
    current_harvested_user = models.ForeignKey('YTUser', related_name='current_harvested_user',  null=True)
    download_videos = models.BooleanField(default=False)
    dev_key = models.TextField(null=True, blank=True, default=DEFAULT_API_APPS['youtube']['dev_key'])
    client = None
    haverst_deque = None

    def update_client_stats(self):
        self.save()

    def end_current_harvest(self):
        self.update_client_stats()
        if self.current_harvested_user:
            self.last_harvested_user = self.current_harvested_user
        super(YoutubeHarvester, self).end_current_harvest()

    @dLogger.debug
    def api_call(self, method, params):
        if debugging: 
            dLogger.log('api_call():')
            dLogger.log('    method: %s'%method)
            dLogger.log('    params: %s'%params)
        if self.client is None:
            raise Exception('You must set the client first!')
        super(YoutubeHarvester, self).api_call(method, params)
        #time.sleep(0.7)
        metp = getattr(self.client, method)
        try:
            ret = metp(**params)
        except HttpError, err:
            if debugging: dLogger.log('    HTTPERROR HAS OCCURED: %s'%err)
            ret = None
        return ret

    def get_last_harvested_user(self):
        return self.last_harvested_user
    
    def get_current_harvested_user(self):
        return self.current_harvested_user  

    @dLogger.debug
    def get_next_user_to_harvest(self): 
        if debugging: dLogger.log("%s::get_next_user_to_harvest()"%self)
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

    @dLogger.debug
    def build_harvester_sequence(self):
        if debugging: dLogger.log("%s::build_harvester_sequence()"%self)
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
        if debugging: dLogger.log("%s::get_stats()"%self)
        parent_stats = super(YoutubeHarvester, self).get_stats()
        parent_stats["concrete"] = {}
        return parent_stats

class YTUser(models.Model):
    '''
    TODO:
    * Implement a Google Plus Profile, which should contain all the personal infos.
        Youtube does not hold personal infos anymore, and a GPlus 
        user can actually have multiple youtube channels.
    * all of the following characteristics are outdated:
        [first_name, last_name, relationship, link, 
        company, occupation, school, hobbies, movies, 
        music, books, hometown, age, gender, location]
    '''

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        if self.title:
            return self.title[:20]+'...'*(len(self.title) > 20)
        elif self.username:
            return self.username[:20]+'...'*(len(self.username) > 20)
        else:
            return u'Unamed User'

    def related_label(self):
        return u"%s (%s)" % (self.username, self.pmk_id)


    pmk_id =  models.AutoField(primary_key=True)
    harvester = models.ForeignKey('YoutubeHarvester', related_name='harvested_users', null=True)

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
    video_count = models.IntegerField(null=True)
    view_count = models.IntegerField(null=True)


    @dLogger.debug
    def update_from_youtube(self, yt_user): #User

        if debugging: 
            dLogger.log("<YTUser: '%s'>::update_from_youtube()"%self)
            #dLogger.log("    yt_user:")
            #dLogger.pretty(yt_user)

        model_changed = False

        if self.fid != yt_user['id']:
            self.fid = yt_user['id']
            model_changed = True

        if 'statistics' in yt_user:
            props = {'subscriber_count': 'subscriberCount',
                    'video_count': 'videoCount',
                    'view_count': 'viewCount'}
            for prop in props:
                if props[prop] in yt_user['statistics'] and \
                getattr(self, prop) != int(yt_user['statistics'][props[prop]]):
                    setattr(self, prop, int(yt_user['statistics'][props[prop]]))
                    model_changed = True

        if 'snippet' in yt_user:
            props = {'description': 'description',
                    'title': 'title'}
            for prop in props:
                if props[prop] in yt_user['snippet'] and \
                getattr(self, prop) != yt_user['snippet'][props[prop]]:
                    setattr(self, prop, yt_user['snippet'][props[prop]])
                    model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            try:
                self.save()
            except:
                self.description = self.description.encode('unicode-escape')
                self.title = self.title.encode('unicode-escape')
                self.save()

        return model_changed


class YTVideo(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        if self.title:
            return self.title[:20]+'...'*(len(self.title) > 20)
        else:
            return 'Untitled video'

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
    duration = models.IntegerField(null=True)

    favorite_count = models.IntegerField(null=True)
    view_count = models.IntegerField(null=True)
    like_count = models.IntegerField(null=True)
    dislike_count = models.IntegerField(null=True)
    comment_count = models.IntegerField(null=True)

    video_file_path = models.TextField(null=True)
    comments_enabled = models.BooleanField(default=True)


    @dLogger.debug
    def update_from_youtube(self, snh_user, yt_video): #Video
        if debugging: dLogger.log("<YTVideo: '%s'>::update_from_youtube()"%self)
        model_changed = False

        fid = yt_video['id']
        if self.fid != fid:
            self.fid = fid
            model_changed = True

        if 'snippet' in yt_video:
            if 'publishedAt' in yt_video['snippet']:
                yt_published = yt_video['snippet']['publishedAt']


            props = {'title':'channelTitle',
                    'description': 'description',
                    'title': 'title' }
            for prop in props:
                if props[prop] in yt_video['snippet'] and \
                getattr(self, prop) != yt_video['snippet'][props[prop]]:
                    setattr(self, prop, yt_video['snippet'][props[prop]])
                    model_changed = True

        if 'statistics' in yt_video:
            props = {'favorite_count':'favoriteCount',
                    'view_count': 'viewCount',
                    'like_count': 'likeCount',
                    'dislike_count': 'dislikeCount',
                    'comment_count': 'commentCount' }
            for prop in props:
                if props[prop] in yt_video['statistics'] and \
                getattr(self, prop) != yt_video['statistics'][props[prop]]:
                    setattr(self, prop, yt_video['statistics'][props[prop]])
                    model_changed = True

        if yt_published:
            date_val = datetime.strptime(yt_published,'%Y-%m-%dT%H:%M:%S.000Z')
            if self.published != date_val:
                self.published = date_val
                model_changed = True

        if 'contentDetails' in yt_video and \
        'duration' in yt_video['contentDetails']:
            rawDuration = yt_video['contentDetails']['duration']

            format = 'PT'
            if 'H' in rawDuration:
                format += '%HH'
            if 'M' in rawDuration:
                format += '%MM'
            if 'S' in rawDuration:
                format += '%SS'
            duration = datetime.strptime(rawDuration, format)
            duration = int((duration-datetime(1900,1,1)).total_seconds())
            if self.duration != duration:
                self.duration = duration
                model_changed = True
        
        if model_changed:
            self.model_update_date = datetime.utcnow()
            #print self.pmk_id, self.fid, self, self.__dict__, yt_video
            try:
                self.save()
            except:
                self.title = self.title.encode('unicode-escape')
                self.description = self.description.encode('unicode-escape')
                self.save()

        return model_changed

class YTVideoCaption(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return '%s caption for %s'%(self.language, self.video)

    pmk_id =  models.AutoField(primary_key=True)

    video = models.ForeignKey('YTVideo', related_name='YTCaptionFiles', null=True)
    srt_file_path = models.TextField(null=True)

    language = models.CharField(max_length=5, null=True)
    auto_generated = models.BooleanField(default=True)

class YTComment(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.message[:20] if self.message else u'Empty message'

    pmk_id =  models.AutoField(primary_key=True)

    fid =  models.CharField(max_length=255, null=True)

    user = models.ForeignKey('YTUser',  related_name='ytcomment.user', null=True)
    video = models.ForeignKey('YTVideo',  related_name='ytcomment.video')
    parent_comment = models.ForeignKey('YTComment', related_name='replies', null=True)
    message = models.TextField(null=True)
    like_count = models.IntegerField(null=True)

    published = models.DateTimeField(null=True)
    updated = models.DateTimeField(null=True)

    @dLogger.debug
    def update_from_youtube(self, snh_video, snh_user, yt_comment): #Comment
        if debugging: 
            dLogger.log("<YTComment: '%s'>::update_from_youtube()"%self)
            #dLogger.pretty(yt_comment)

        model_changed = False

        fid = yt_comment['id']

        if self.fid != fid:
            self.fid = fid
            model_changed = True

        snippet = yt_comment['snippet']

        if self.video != snh_video:
            self.video = snh_video
            model_changed = True

        if self.user != snh_user:
            self.user = snh_user
            model_changed = True

        yt_published = snippet['publishedAt']
        date_val = datetime.strptime(yt_published[:-5],'%Y-%m-%dT%H:%M:%S')
        if self.published != date_val:
            self.published = date_val
            model_changed = True

        yt_updated = snippet['updatedAt']
        date_val = datetime.strptime(yt_updated[:-5],'%Y-%m-%dT%H:%M:%S')
        if self.updated != date_val:
            self.updated = date_val
            model_changed = True

        content = snippet['textDisplay'].encode('unicode_escape')
        content = re.sub(r'\\\\x..', '', content)
        if self.message != content:
            self.message = content
            model_changed = True

        like_count = snippet['likeCount']
        if self.like_count != like_count:
            self.like_count = like_count   
            model_changed = True        

        if model_changed:
            self.model_update_date = datetime.utcnow()
            try:
                self.save()
            except Exception, e:
                dLogger.log('    Error while saving:')
                dLogger.exception(e)
                dLogger.pretty(str(yt_comment).encode('unicode_escape'))
        return model_changed









