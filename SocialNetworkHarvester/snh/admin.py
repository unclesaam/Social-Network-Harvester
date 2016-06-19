# coding=UTF-8

from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models

from snh.models.twittermodel import TWUser, TWSearch, TWStatus, TwitterHarvester
from snh.models.facebookmodel import FBUser, FacebookHarvester, FBPost, FBComment
from snh.models.dailymotionmodel import DMUser, DailyMotionHarvester
from snh.models.youtubemodel import YTUser, YTVideo, YoutubeHarvester
from django.contrib.auth.models import User as BaseUser
from fandjango.models import User as FanUser, OAuthToken
from settings import dLogger

#############
class TwitterHarvesterAdmin(admin.ModelAdmin):
    fieldsets = (
        ('', {
            'fields': (
                u'harvester_name', 
                u'is_active', 
                u'keep_raw_statuses',
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

    raw_id_fields = ('twusers_to_harvest','twsearch_to_harvest',)
    related_lookup_fields = {'m2m': ['twusers_to_harvest','twsearch_to_harvest',],}
    '''
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "twusers_to_harvest":
            conditionList = [models.Q(fid__isnull=True), models.Q(followers_count__gte=1000)]
            kwargs["queryset"] = TWUser.objects.filter(reduce(lambda x, y: x | y, conditionList)).distinct()
        return super(TwitterHarvesterAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
    '''
    #filter_horizontal = ('twusers_to_harvest','twsearch_to_harvest',)

class TWUserAdmin(admin.ModelAdmin):
    search_fields = ('screen_name',)
    readonly_fields = (
                'model_update_date',
                            'lang', 
                            'description',
                            'location', 
                            'favourites_count', 
                            'followers_count', 
                            'friends_count', 
                            'statuses_count',
                            'harvester'
                        )
    fieldsets = (   (None, {
                        'fields': (
                'screen_name',
                            'error_triggered'
                        )
                    }),
                    ('Détails', {
                        'fields': (
                            'harvester',
                            'lang',
                            'model_update_date',
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
                            u'app_id',
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

    raw_id_fields = ('fbusers_to_harvest',)
    related_lookup_fields = {'m2m': ['fbusers_to_harvest',],}
    '''
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "fbusers_to_harvest":
            kwargs["queryset"] = FBUser.objects.exclude(username__isnull=True)
        return super(FacebookHarvesterAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    filter_horizontal = ('fbusers_to_harvest',)
    '''

class FBUserAdmin(admin.ModelAdmin):
    list_per_page = 500
    fields = [
                u'fid',
                u'username', 
                u'error_triggered', 
            ]
    list_display = ('name','username','fid')
    search_fields = ('username','fid','name')

class FBPostAdmin(admin.ModelAdmin):
    list_per_page = 500
    readonly_fields = (
                'user',
                'fid',
                'message',
                'message_tags_raw',
                'picture',
                'link',
                'name',
                'caption',
                'description',
                'source',
                'properties_raw',
                'icon',
                'privacy_raw',
                'ftype',
                'likes_from',
                'likes_count',
                'comments_count',
                'shares_count',
                'place_raw',
                'story',
                'story_tags_raw',
                'object_id',
                'application_raw',
                'created_time',
                'updated_time',
                'error_on_update',
                        )
    fields = [
                'user',
                'fid',
                'message',
                'message_tags_raw',
                'picture',
                'link',
                'name',
                'caption',
                'description',
                'source',
                'properties_raw',
                'icon',
                'privacy_raw',
                'ftype',
                'likes_from',
                'likes_count',
                'comments_count',
                'shares_count',
                'place_raw',
                'story',
                'story_tags_raw',
                'object_id',
                'application_raw',
                'created_time',
                'updated_time',
                'error_on_update',
            ]
    list_display = ('fid', 'user', 'message', 'ftype')

class FBCommentAdmin(admin.ModelAdmin):
    list_per_page = 100
    readonly_fields = [
                'fid',
                'ffrom',
                'message',
                'created_time',
                'likes',
                'user_likes',
                'ftype',
                'post',
                'error_on_update',
            ]
    fields = [
                'fid',
                'ffrom',
                'message',
                'created_time',
                'likes',
                'user_likes',
                'ftype',
                'post',
                'error_on_update',
            ]
    list_display = ('fid', 'ffrom', 'message', 'ftype')

admin.site.register(FacebookHarvester, FacebookHarvesterAdmin)
admin.site.register(FBUser, FBUserAdmin)
admin.site.register(FBPost, FBPostAdmin)
admin.site.register(FBComment, FBCommentAdmin)


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
    #raw_id_fields = ('dmusers_to_harvest',)
    # define the related_lookup_fields
    #related_lookup_fields = {
    #    'm2m': ['dmusers_to_harvest',],
    #}
    filter_horizontal = ('dmusers_to_harvest',)

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
                        u'download_videos',
                        u'max_retry_on_fail',
                        u'harvest_window_from',
                        u'harvest_window_to'
                        ),
        }),
        ('Users to harvest', {
            'classes': ('collapse open',),
            'fields' : ('ytusers_to_harvest',),
        }),
    )
    raw_id_fields = ('ytusers_to_harvest',)
    related_lookup_fields = {'m2m': ['ytusers_to_harvest', ], }

    '''
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "ytusers_to_harvest":
            kwargs["queryset"] = YTUser.objects.filter(username__isnull=False)
        return super(YoutubeHarvesterAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
    filter_horizontal = ('ytusers_to_harvest',)
    '''

class YTUserAdmin(admin.ModelAdmin):
    readonly_fields = (
            'subscriber_count',
            'video_count',
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
                u'video_count',
                u'view_count'
                )
            }
        )
    )
    list_display = ('username',)
    search_fields = ('username',)

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
