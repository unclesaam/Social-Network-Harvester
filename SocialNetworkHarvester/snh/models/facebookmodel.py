# coding=UTF-8
from collections import deque
import datetime
import time
import re
import json

from django.db import models, IntegrityError
from snh.models.common import *
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

import snhlogger
logger = snhlogger.init_logger(__name__, "facebook_model.log")

from settings import DEBUGCONTROL, dLogger
debugging = DEBUGCONTROL['facebookmodel']
if debugging: print "DEBBUGING ENABLED IN %s"%__name__

class FacebookHarvester(AbstractHaverster):

    class Meta:
        app_label = "snh"

    app_id = models.CharField(max_length=255) #TODO: permettre que chaque Harvester aie sa propre app.
    client = None
    fbusers_to_harvest = models.ManyToManyField('FBUser', related_name='fbusers_to_harvest')
    update_likes = models.BooleanField()

    #a bug or my limited knowledge of the framework.. cannot import fandjango.models here :(
    def set_client(self, client):
        self.client = client

    def get_client(self):
        if self.client is None:
            raise Exception("you need to set the client!!")
        return self.client

    def end_current_harvest(self):
        super(FacebookHarvester, self).end_current_harvest()

    @dLogger.debug
    def api_call(self, method, params):
        if debugging: 
            dLogger.log("<FacebookHarvester>::api_call()")
            dLogger.log("    method: %s"%(method))
            dLogger.log("    params: %s"%(params))

        super(FacebookHarvester, self).api_call(method, params)
        c = self.get_client()   
        metp = getattr(c, method)
        ret = metp(**params)
        #if debugging: dLogger.log("    ret: %s"%(ret))
        return ret 


    def get_last_harvested_user(self):
        return None
    
    def get_current_harvested_user(self):
        return None

    def get_next_user_to_harvest(self):
        return None

    @dLogger.debug
    def get_stats(self):
        parent_stats = super(FacebookHarvester, self).get_stats()
        return parent_stats


class FacebookSessionKey(models.Model):
    ''' Stores a key returned by the authentification of a user through the Facebook javascript sdk.
        Normally, there should be only one instance of FacebookSessionKey per server.
    '''
    user_access_token = models.CharField(max_length=255, null=True)
    updated_time = models.DateTimeField(null=True)

    class Meta:
        app_label = "snh" 

    def get_access_token(self):
        return self.user_access_token

    @dLogger.debug
    def set_access_token(self, accessToken):
        if debugging: dLogger.log("<FacebookSessionKey>::set_access_token()")
        self.user_access_token = accessToken
        self.updated_time = datetime.utcnow()
        self.save()

    def get_last_update_time(self):
        return self.updated_time


class FBResult(models.Model):
    ''' FBResult is used to temporarily store the raw data obtained from Facebook graph API batch methods.
        Can either contain a FBPost, FBComment or FBPost.likes raw page to be analysed later.
    '''
    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return unicode(self.fid)   

    harvester = models.ForeignKey("FacebookHarvester")
    result = models.TextField(null=True)
    fid = models.TextField(null=True)
    ftype = models.TextField(null=True)
    parent = models.TextField(null=True)

class FBUser(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return unicode(self.username if self.username else self.name)

    def related_label(self):
        return u"%s (%s)" % (self.username if self.username else self.name, self.pmk_id)
   
    pmk_id =  models.AutoField(primary_key=True)

    fid = models.CharField(max_length=255, null=True, unique=True)
    name = models.CharField(max_length=255, null=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    website = models.ForeignKey('URL', related_name="fbuser.website", null=True)
    link = models.ForeignKey('URL', related_name="fbuser.link", null=True)

    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    gender = models.CharField(max_length=255, null=True)
    locale = models.CharField(max_length=255, null=True)
    languages_raw = models.TextField(null=True) #not supported but saved
    third_party_id = models.CharField(max_length=255, null=True)
    installed_raw = models.TextField(null=True) #not supported but saved
    timezone_raw = models.TextField(null=True) #not supported but saved
    updated_time = models.DateTimeField(null=True)
    verified = models.BooleanField()
    bio = models.TextField(null=True)
    birthday = models.DateTimeField(null=True)
    education_raw = models.TextField(null=True) #not supported but saved
    email = models.CharField(max_length=255, null=True)
    hometown = models.CharField(max_length=255, null=True)
    interested_in_raw = models.TextField(null=True) #not supported but saved
    location_raw = models.TextField(null=True) #not supported but saved
    political = models.TextField(null=True)
    favorite_athletes_raw = models.TextField(null=True) #not supported but saved
    favorite_teams_raw = models.TextField(null=True) #not supported but saved
    quotes = models.TextField(max_length=255, null=True)
    relationship_status = models.TextField(null=True)
    religion = models.TextField(null=True)
    significant_other_raw = models.TextField(null=True) #not supported but saved
    video_upload_limits_raw = models.TextField(null=True) #not supported but saved
    work_raw = models.TextField(null=True) #not supported but saved

    category = models.TextField(null=True)
    likes = models.IntegerField(null=True)
    about = models.TextField(null=True)
    phone = models.CharField(max_length=255, null=True)
    checkins = models.IntegerField(null=True)
    picture = models.ForeignKey('URL', related_name="fbpagedesc.picture", null=True)
    talking_about_count = models.IntegerField(null=True)

    error_triggered = models.BooleanField()
    error_on_update = models.BooleanField()

    @dLogger.debug
    def update_url_fk(self, self_prop, face_prop, facebook_model):
        if debugging: dLogger.log("<FBUser: %s>::update_url_fk(%s)"%(self.name, face_prop))

        model_changed = False
        if face_prop in facebook_model:
            prop_val = facebook_model[face_prop]
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
        if debugging: dLogger.log("    has changed: %s"%model_changed)
        return model_changed, self_prop

    @dLogger.debug
    def update_from_facebook(self, fb_user):
        if debugging: 
            dLogger.log("<FBUser: %s>::update_from_facebook()"%self.name)
            #dLogger.log("    fb_user: %s"%fb_user)

        if 'body' in fb_user:
            fb_user = json.loads(fb_user['body'])
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"name":u"name",
                            u"username":u"username",
                            u"first_name":u"first_name",
                            u"last_name":u"last_name",
                            u"gender":u"gender",
                            u"locale":u"locale",
                            u"languages_raw":u"languages",
                            u"third_party_id":u"third_party_id",
                            u"installed_raw":u"installed",
                            u"timezone_raw":u"timezone",
                            u"verified":u"verified",
                            u"bio":u"bio",
                            u"education_raw":u"educaction",
                            u"email":u"email",
                            u"hometown":u"hometown",
                            u"interested_in_raw":u"interested_in",
                            u"location_raw":u"location",
                            u"political":u"political",
                            u"favorite_athletes_raw":u"favorite_athletes",
                            u"favorite_teams":u"favorite_teams",
                            u"quotes":u"quotes",
                            u"relationship_status":u"relationship_status",
                            u"religion":u"religion",
                            u"significant_other_raw":u"significant_other",
                            u"video_upload_limits_raw":u"video_upload_limits",
                            u"work_raw":u"work",
                            u"category":u"category",
                            u"likes":u"likes",
                            u"location_raw":u"location",
                            u"phone":u"phone",
                            u"checkins":u"checkins",
                            u"about":u"about",
                            u"talking_about_count":u"talking_about_count",
                            }

        #date_to_check = {"birthday":"birthday"}
        date_to_check = {}

        for prop in props_to_check:
            #if debugging: dLogger.log("    props_to_check[prop]: %s"%props_to_check[prop])
            if props_to_check[prop] in fb_user and unicode(self.__dict__[prop]) != unicode(fb_user[props_to_check[prop]]):
                #if debugging: dLogger.log("    fb_user[props_to_check[%s]]: %s"%(props_to_check[prop], fb_user[props_to_check[prop]]))
                self.__dict__[prop] = fb_user[props_to_check[prop]]
                #print "prop changed. %s = %s" % (prop, self.__dict__[prop])
                model_changed = True
                if debugging: dLogger.log("    %s has been updated"%prop)

        for prop in date_to_check:
            if date_to_check[prop] in fb_user and self.__dict__[prop] != fb_user[date_to_check[prop]]:
                date_val = datetime.strptime(fb_user[prop],'%m/%d/%Y')
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True

        (changed, self_prop) = self.update_url_fk(self.website, "website", fb_user)
        if changed:
            self.website = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.link, "link", fb_user)
        if changed:
            self.link = self_prop
            model_changed = True

        (changed, self_prop) = self.update_url_fk(self.picture, "picture", fb_user)
        if changed:
            self.picture = self_prop
            model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.error_on_update = False
            #print self.pmk_id, self.fid, self
            self.save()
            if debugging: dLogger.log("    updated data!")

        return model_changed

class FBPost(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return "%s - %s"%(self.user, self.ftype)

    pmk_id =  models.AutoField(primary_key=True)
    user = models.ForeignKey('FBUser')

    fid = models.CharField(max_length=255, null=True, unique=True)
    ffrom = models.ForeignKey('FBUser', related_name='fbpost.from', null=True)
    #to = models.ManyToManyField('FBUser', related_name='fbpost.to', null=True)
    message = models.TextField(null=True)
    message_tags_raw = models.TextField(null=True) #not supported but saved
    picture = models.ForeignKey('URL', related_name="fbpost.picture", null=True)
    link = models.ForeignKey('URL', related_name="fbpost.link", null=True)
    name = models.CharField(max_length=255, null=True)
    caption = models.TextField(null=True)
    description = models.TextField(null=True)
    source = models.ForeignKey('URL', related_name="fbpost.source", null=True)
    properties_raw = models.TextField(null=True) #not supported but saved
    icon = models.ForeignKey('URL', related_name="fbpost.icon", null=True)
    #actions = array of objects containing the name and link #will not be supported
    privacy_raw = models.TextField(null=True) #not supported but saved
    ftype = models.CharField(max_length=255, null=True)
    likes_from = models.ManyToManyField('FBUser', related_name='fbpost.likes_from', null=True)
    likes_count = models.IntegerField(null=True)
    comments_count = models.IntegerField(null=True)
    shares_count = models.IntegerField(null=True)
    place_raw = models.TextField(null=True) #not supported but saved 
    story =  models.TextField(null=True)
    story_tags_raw = models.TextField(null=True) #not supported but saved 
    object_id = models.BigIntegerField(null=True)
    application_raw = models.TextField(null=True) #not supported but saved 
    created_time = models.DateTimeField(null=True)
    updated_time = models.DateTimeField(null=True)
    error_on_update = models.BooleanField()

    @dLogger.debug
    def get_existing_user(self, param):
        if debugging: dLogger.log("<FBPost: %s>::get_existing_user()"%self.fid)

        user = None
        try:
            user = FBUser.objects.get(**param)
        except MultipleObjectsReturned:
            logger.debug(u">>>>MULTIPLE USER")
            user = FBUser.objects.filter(**param)[0]
        except ObjectDoesNotExist:
            logger.debug(u">>>>DOES NOT EXISTS")
            pass
        if debugging: dLogger.log("    user returned: %s"%user)
        return user

    @dLogger.debug
    def update_url_fk(self, self_prop, face_prop, facebook_model):
        if debugging: dLogger.log("<FBPost: %s>::update_url_fk()"%self.fid)

        model_changed = False
        if face_prop in facebook_model:
            prop_val = facebook_model[face_prop]
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

    @dLogger.debug
    def update_user_fk(self, self_prop, face_prop, facebook_model):
        if debugging: dLogger.log("<FBPost: %s>::update_user_fk()"%self.fid)

        model_changed = False
        if face_prop in facebook_model:
            prop_val = facebook_model[face_prop]
            if prop_val and (self_prop is None or self_prop.fid != prop_val["id"]):
                user = None
                user = self.get_existing_user({"fid__exact":prop_val["id"]})
                if not user:
                    try:
                        user = FBUser()
                        user.update_from_facebook(prop_val)
                    except IntegrityError:
                        user = self.get_existing_user({"fid__exact":prop_val["id"]})
                        if user:
                            user.update_from_facebook(prop_val)
                        else:
                            logger.debug(u">>>>CRITICAL CANT UPDATED DUPLICATED USER %s" % prop_val["id"])
                        
                self_prop = user
                #print self_prop, user.name, prop_val
                model_changed = True

        return model_changed, self_prop

    @dLogger.debug
    def update_likes_from_facebook(self, likes):
        if debugging: dLogger.log("<FBPost: %s>::update_likes_from_facebook()"%self.fid)

        model_changed = False

        for fbuser in likes:
            if self.likes_from.filter(fid__exact=fbuser["id"]).count() == 0:
                user_like = None
                user_like = self.get_existing_user({"fid__exact":fbuser["id"]})
                if not user_like:
                    try:
                        user_like = FBUser(fid=fbuser["id"])
                        user_like.save()
                    except IntegrityError:
                        user_like = self.get_existing_user({"fid__exact":fbuser["id"]})
                        if user_like:
                            user_like.update_from_facebook(fbuser)
                        else:
                            logger.debug(u">>>>CRITICAL CANT UPDATED DUPLICATED USER %s" % fbuser["id"])

                user_like.update_from_facebook(fbuser)

                if user_like not in self.likes_from.all():
                    self.likes_from.add(user_like)
                    model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.error_on_update = False
            self.save()
            if debugging: dLogger.log("    updated data!")
   
        return model_changed

    @dLogger.debug
    def update_from_facebook(self, facebook_model, user):
        if debugging: 
            dLogger.log("<FBPost: %s>::update_from_facebook()"%self.fid)
            #dLogger.log("    facebook_model: %s"%facebook_model)

        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"message":u"message",
                            u"message_tags_raw":u"message_tags",
                            u"name":u"name",
                            u"caption":u"caption",
                            u"description":u"description",
                            u"description":u"subject",
                            u"properties_raw":u"properties",
                            u"privacy_raw":u"privacy",
                            u"ftype":u"type",
                            u"place_raw":u"place",
                            u"story":u"story",
                            u"story_tags_raw":u"story_tags",
                            u"object_id":u"object_id",
                            u"application_raw":u"application",
                            }

        subitem_to_check = {
                            u"likes_count":[u"likes",u"count"],
                            u"comments_count":[u"comments",u"count"],
                            u"shares_count":[u"shares",u"count"],
                            }

        date_to_check = [u"created_time", u"updated_time"]

        self.user = user

        for prop in props_to_check:
            #if debugging: dLogger.log("    prop: %s"%prop)
            if props_to_check[prop] in facebook_model and self.__dict__[prop] != facebook_model[props_to_check[prop]]:
                #if debugging: dLogger.log("    facebook_model[%s]: %s"%(props_to_check[prop], facebook_model[props_to_check[prop]]))
                self.__dict__[prop] = facebook_model[props_to_check[prop]]
                model_changed = True
                if debugging: dLogger.log("    %s has been updated"%prop)

        for prop in subitem_to_check:
            subprop = subitem_to_check[prop]
            #logger.debug("DEVED:%s, %s, %s" % (prop, subprop, facebook))
            if subprop[0] in facebook_model and \
                    type(facebook_model[subprop[0]]) is dict and \
                    subprop[1] in facebook_model[subprop[0]] and \
                    self.__dict__[prop] != facebook_model[subprop[0]][subprop[1]]:
                self.__dict__[prop] = facebook_model[subprop[0]][subprop[1]]
                model_changed = True
            elif prop == "likes_count" and \
                    "likes" in facebook_model and \
                    type(facebook_model["likes"]) is int:
                self.__dict__["likes_count"] = facebook_model[subprop[0]]
                model_changed = True
                

        for prop in date_to_check:
            if prop in facebook_model:
                fb_val = facebook_model[prop]
                date_val = datetime.strptime(fb_val,'%Y-%m-%dT%H:%M:%S+0000')
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True

        (changed, self_prop) = self.update_url_fk(self.picture, "picture", facebook_model)
        if changed:
            self.picture = self_prop
            model_changed = True

        (changed, self_prop) = self.update_url_fk(self.link, "link", facebook_model)
        if changed:
            self.link = self_prop
            model_changed = True

        (changed, self_prop) = self.update_url_fk(self.source, "source", facebook_model)
        if changed:
            self.source = self_prop
            model_changed = True

        (changed, self_prop) = self.update_url_fk(self.icon, "icon", facebook_model)
        if changed:
            self.icon = self_prop
            model_changed = True

        (changed, self_prop) = self.update_user_fk(self.ffrom, "from", facebook_model)
        if changed:
            self.ffrom = self_prop
            model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.error_on_update = False
            self.save()
   
        return model_changed
        
class FBComment(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.message

    pmk_id =  models.AutoField(primary_key=True)

    fid = models.CharField(max_length=255, null=True, unique=True)
    ffrom = models.ForeignKey('FBUser', related_name="fbcomment.ffrom", null=True)
    message = models.TextField(null=True)
    created_time = models.DateTimeField(null=True)
    likes = models.IntegerField(null=True)
    user_likes = models.IntegerField(null=True)
    ftype = models.CharField(max_length=255, null=True)

    post = models.ForeignKey('FBPost', null=True)

    error_on_update = models.BooleanField()

    @dLogger.debug
    def get_existing_user(self, param):
        if debugging: dLogger.log("<FBComment: %s>::get_existing_user()"%self.fid)

        user = None
        try:
            user = FBUser.objects.get(**param)
        except MultipleObjectsReturned:
            user = FBUser.objects.filter(**param)[0]
        except ObjectDoesNotExist:
            pass
        return user

    @dLogger.debug
    def update_user_fk(self, self_prop, face_prop, facebook_model):
        if debugging: dLogger.log("<FBComment: %s>::update_user_fk()"%self.fid)

        model_changed = False
        if face_prop in facebook_model:
            prop_val = facebook_model[face_prop]
            if prop_val and (self_prop is None or self_prop.fid != prop_val["id"]):
                user = None
                user = self.get_existing_user({"fid__exact":prop_val["id"]})

                if not user:
                    try:
                        user = FBUser()
                        user.update_from_facebook(prop_val)
                    except IntegrityError:
                        user = self.get_existing_user({"fid__exact":prop_val["id"]})
                        if user:
                            user.update_from_facebook(prop_val)
                        else:
                            logger.debug(u">>>>CRITICAL CANT UPDATED DUPLICATED USER %s" % prop_val["id"])

                self_prop = user
                model_changed = True

        return model_changed, self_prop

    @dLogger.debug
    def update_from_facebook(self, facebook_model, status):
        if debugging: dLogger.log("<FBComment: %s>::update_from_facebook()"%self.fid)

        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"message":u"message",
                            u"likes":u"like_count",
                            u"user_likes":u"user_likes",
                            u"ftype":u"type",
                            }


        date_to_check = [u"created_time"]

        self.post = status

        if  self.fid is None and "id" in facebook_model:
            self.fid =  facebook_model["id"]
            model_changed = True

        for prop in props_to_check:
            if props_to_check[prop] in facebook_model and self.__dict__[prop] != facebook_model[props_to_check[prop]]:
                self.__dict__[prop] = unicode(facebook_model[props_to_check[prop]])
                model_changed = True
                if debugging: dLogger.log("    %s has been updated"%prop)
        
        for prop in date_to_check:
            fb_val = facebook_model[prop]
            date_val = datetime.strptime(fb_val,'%Y-%m-%dT%H:%M:%S+0000')
            if self.__dict__[prop] != date_val:
                self.__dict__[prop] = date_val
                model_changed = True

        (changed, self_prop) = self.update_user_fk(self.ffrom, "from", facebook_model)
        if changed:
            self.ffrom = self_prop
            model_changed = True

        if model_changed:

            self.model_update_date = datetime.utcnow()
            self.error_on_update = False
            #logger.debug(u"FBComment exist and changed! %s" % (self.fid))
            try:
                self.save()
                if debugging: dLogger.log("    updated data!")
            except :
                if debugging: 
                    dLogger.log("    message from model: %s"%facebook_model['message'])
                    self.message = facebook_model['message']
                    dLogger.log("    message before conversion: %s"%self.message)
                self.message = unicode(self.message)
                if debugging: dLogger.log("    message after conversion: %s"%unicode(self.message))
                self.save()
        #else:
        #    logger.debug(u">>>>>>>>>>>>>>>>>>FBComment exist and unchanged! %s" % (self.fid))
            
   
        return model_changed

