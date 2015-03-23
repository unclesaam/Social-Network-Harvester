# coding=UTF-8

from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models

from snh.models.twittermodel import TwitterHarvester
from snh.models.twittermodel import TWUser, TWSearch, TWStatus

from snh.models.facebookmodel import FacebookHarvester
from snh.models.facebookmodel import FBUser

from snh.models.dailymotionmodel import DailyMotionHarvester
from snh.models.dailymotionmodel import DMUser

from snh.models.youtubemodel import YoutubeHarvester
from snh.models.youtubemodel import YTUser
#############
class TwitterHarvesterAdmin(admin.ModelAdmin):

    fieldsets = (
        ('', {
            'fields': (
                            u'harvester_name', 
                            u'is_active', 
                            u'consumer_key',
                            u'consumer_secret',
                            u'access_token_key',
                            u'access_token_secret',
                            u'max_retry_on_fail',
                            u'harvest_window_from',
                            u'harvest_window_to',
                        ),
        }),
        ('Users to harvest', {
            'classes': ('collapse open',),
            'fields' : ('twusers_to_harvest',),
        }),
        ('Searches to harvest', {
            'classes': ('collapse open',),
            'fields' : ('twsearch_to_harvest',),
        }),
    )

    # define the raw_id_fields
    raw_id_fields = ('twusers_to_harvest','twsearch_to_harvest',)
    # define the related_lookup_fields
    related_lookup_fields = {
        'm2m': ['twusers_to_harvest','twsearch_to_harvest',],
    }

class TWUserAdmin(admin.ModelAdmin):
    fields = [
                u'screen_name', 
                u'error_triggered', 
            ]

class TWSearchAdmin(admin.ModelAdmin):
    fields = [
                u'term', 
            ]
class TWStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'text')
    search_fields = ('text',)
    fields = [
                u'user',
                #u'fid',
                u'created_at',
                u'favorited',
                u'retweet_count',
                #u'retweeted',
                u'source',
                u'text',
                u'truncated',
                u'hash_tags',
                u'user_mentions',
                #u'model_update_date',
                #u'error_on_update',
            ]
    filter_horizontal = ('hash_tags','user_mentions')

admin.site.register(TWStatus, TWStatusAdmin)

admin.site.register(TwitterHarvester, TwitterHarvesterAdmin)
admin.site.register(TWUser, TWUserAdmin)
admin.site.register(TWSearch, TWSearchAdmin)

##############
class FacebookHarvesterAdmin(admin.ModelAdmin):

    fieldsets = (
        ('', {
            'fields': (
                            u'harvester_name', 
                            u'is_active', 
                            u'update_likes',
                            u'max_retry_on_fail',
                            u'harvest_window_from',
                            u'harvest_window_to',
                        ),
        }),
        ('Users to harvest', {
            'classes': ('collapse open',),
            'fields' : ('fbusers_to_harvest',),
        }),
    )

    # define the raw_id_fields
    raw_id_fields = ('fbusers_to_harvest',)
    # define the related_lookup_fields
    related_lookup_fields = {
        'm2m': ['fbusers_to_harvest',],
    }


class FBUserAdmin(admin.ModelAdmin):
    fields = [
                u'username', 
                u'error_triggered', 
            ]

admin.site.register(FacebookHarvester, FacebookHarvesterAdmin)
admin.site.register(FBUser, FBUserAdmin)

##############
class DailyMotionHarvesterAdmin(admin.ModelAdmin):

    fieldsets = (
        ('', {
            'fields': (
                        u'harvester_name', 
                        u'key', 
                        u'secret', 
                        u'user', 
                        u'password', 
                        u'is_active',
                        u'max_retry_on_fail',
                        u'harvest_window_from',
                        u'harvest_window_to',
                        ),
        }),
        ('Users to harvest', {
            'classes': ('collapse open',),
            'fields' : ('dmusers_to_harvest',),
        }),
    )

    # define the raw_id_fields
    raw_id_fields = ('dmusers_to_harvest',)
    # define the related_lookup_fields
    related_lookup_fields = {
        'm2m': ['dmusers_to_harvest',],
    }

class DMUserAdmin(admin.ModelAdmin):
    fields = [
                u'username',
            ]

admin.site.register(DailyMotionHarvester, DailyMotionHarvesterAdmin)
admin.site.register(DMUser, DMUserAdmin)

##############
class YoutubeHarvesterAdmin(admin.ModelAdmin):

    fieldsets = (
        ('', {
            'fields': (
                        u'harvester_name', 
                        u'dev_key', 
                        u'is_active',
                        u'max_retry_on_fail',
                        u'harvest_window_from',
                        u'harvest_window_to',
                        ),
        }),
        ('Users to harvest', {
            'classes': ('collapse open',),
            'fields' : ('ytusers_to_harvest',),
        }),
    )

    # define the raw_id_fields
    raw_id_fields = ('ytusers_to_harvest',)
    # define the related_lookup_fields
    related_lookup_fields = {
        'm2m': ['ytusers_to_harvest',],
    }

class YTUserAdmin(admin.ModelAdmin):
    fields = [
                u'username', 
            ]

admin.site.register(YoutubeHarvester, YoutubeHarvesterAdmin)
admin.site.register(YTUser, YTUserAdmin)

