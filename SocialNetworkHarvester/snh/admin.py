# coding=UTF-8

from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models

from snh.models.twittermodel import TWUser, TWSearch, TWStatus, TwitterHarvester
from snh.models.facebookmodel import FBUser, FacebookHarvester
from snh.models.dailymotionmodel import DMUser, DailyMotionHarvester
from snh.models.youtubemodel import YTUser, YTVideo, YoutubeHarvester

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
    search_fields = ('screen_name',)
    readonly_fields = (
                            'screen_name',
                            'lang', 
                            'description',
                            'location', 
                            'favourites_count', 
                            'followers_count', 
                            'friends_count', 
                            'statuses_count'
                        )
    fieldsets = (   (None, {
                        'fields': (
                            'error_triggered', 
                            'model_update_date'
                        )
                    }),
                    ('Détails', {
                        'fields': (
                            'screen_name',
                            'lang', 
                            'description',
                            'location', 
                            'favourites_count', 
                            'followers_count', 
                            'friends_count', 
                            'statuses_count'
                        )
                    }),
                )


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
        (None, {
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
    readonly_fields = (
            'subscriber_count',
            'video_watch_count',
            'view_count'
    )
    fieldsets = (   
        (None,    {
            u'fields': (
                u'username',
                )
            }
        ),
        (u'Détails', {
            u'fields': (  
                u'subscriber_count',
                u'video_watch_count',
                u'view_count'
                )
            }
        )
    )

class YTVideoAdmin(admin.ModelAdmin):
    readonly_fields = (
            'user',
            'fid',
            'url',
            'player_url',
            'swf_url',
            'title',
            'published',
            'updated',
            'recorded',
            'description',
            'category',
            'favorite_count',
            'view_count',
            'duration',
    )
    fieldsets = (   
        (None,    {
            u'fields': (
                'user',
                'fid',
                'url',
                'player_url',
                'swf_url',
                'title',
                'published',
                'updated',
                'recorded',
                'description',
                'category',
                'favorite_count',
                'view_count',
                'duration',
                )
            }
        ),
    )

admin.site.register(YoutubeHarvester, YoutubeHarvesterAdmin)
admin.site.register(YTUser, YTUserAdmin)
admin.site.register(YTVideo, YTVideoAdmin)