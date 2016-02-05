# coding=UTF-8

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('snh.views',

    #ROOT
    (r'^$', 'index'),
    (r'^toggle_harvester$', 'toggle_harvester'),


    #TWITTER
    (r'^tw/(?P<harvester_id>\d+)$', 'tw'),
    (r'^tw_user_detail/(?P<harvester_id>\d+)/(?P<screen_name>\w+)/$', 'tw_user_detail'),
    (r'^tw_search_detail/(?P<harvester_id>\d+)/(?P<search_id>\d+)/$', 'tw_search_detail'),
    (r'^tw_status_detail/(?P<harvester_id>\d+)/(?P<status_id>\d+)/$', 'tw_status_detail'),
    #TWITTER AJAX
    (r'^get_tw_list/(?P<call_type>[\w\.]+)/(?P<harvester_id>\d+)/$', 'get_tw_list'),
    (r'^get_twsearch_list/(?P<call_type>[\w\.]+)/(?P<harvester_id>\d+)/$', 'get_twsearch_list'),
    (r'^get_tw_status_list/(?P<call_type>[\w\.]+)/(?P<screen_name>\w+)/$', 'get_tw_status_list'),
    (r'^get_tw_harvester_status_list/(?P<call_type>[\w\.]+)/(?P<harvester_id>\w+)/$', 'get_tw_harvester_status_list'),
    (r'^get_tw_statussearch_list/(?P<call_type>[\w\.]+)/(?P<screen_name>\w+)/$', 'get_tw_statussearch_list'),
    (r'^get_tw_searchdetail_list/(?P<call_type>[\w\.]+)/(?P<search_id>\d+)/$', 'get_tw_searchdetail_list'),

    (r'^get_tw_status_json/', 'get_tw_status_json'),
    (r'^dwld_tw_status_csv/', 'dwld_tw_status_csv'),

    (r'^get_status_chart/(?P<harvester_id>\d+)/(?P<screen_name>\w+)/$', 'get_status_chart'),
    (r'^get_at_chart/(?P<harvester_id>\d+)/(?P<screen_name>\w+)/$', 'get_at_chart'),
    (r'^get_search_status_chart/(?P<harvester_id>\d+)/(?P<search_term>\w+)/$', 'get_search_status_chart'),

    #FACEBOOK
    (r'^request_fb_token$', 'request_fb_token'),
    (r'^test_fb_token$', 'test_fb_token'),
    (r'^fb/(?P<harvester_id>\d+)$', 'fb'),
    (r'^fb_user_detail/(?P<harvester_id>\d+)/(?P<username>[\w\.]+)/$', 'fb_user_detail'),
    (r'^fb_user_detail/(?P<harvester_id>\d+)/fid/(?P<userfid>[\w\.]+)/$', 'fb_userfid_detail'),
    (r'^fb_post_detail/(?P<harvester_id>\d+)/(?P<post_id>[\w\.]+)/$', 'fb_post_detail'),
    #FACEBOOK UPDATE USER TOKEN
    (r'fb_update_client_token', 'fb_update_client_token'),
    #FACEBOOK AJAX
    (r'^get_fb_list/(?P<call_type>[\w\.]+)/(?P<harvester_id>\d+)/$', 'get_fb_list'),
    (r'^get_fb_post_list/(?P<call_type>[\w\.]+)/(?P<userfid>[\w\.]+)/$', 'get_fb_post_list'),
    (r'^get_fb_harvester_post_list/(?P<call_type>[\w\.]+)/(?P<harvester_id>[\w\.]+)/$', 'get_fb_harvester_post_list'),
    (r'^get_fb_otherpost_list/(?P<call_type>[\w\.]+)/(?P<userfid>[\w\.]+)/$', 'get_fb_otherpost_list'),
    (r'^get_fb_comment_list/(?P<call_type>[\w\.]+)/(?P<userfid>[\w\.]+)/$', 'get_fb_comment_list'),
    (r'^get_fb_harvester_comment_list/(?P<call_type>[\w\.]+)/(?P<harvester_id>[\w\.]+)/$', 'get_fb_harvester_comment_list'),
    (r'^get_fb_postcomment_list/(?P<call_type>[\w\.]+)/(?P<postfid>[\w\.]+)/$', 'get_fb_postcomment_list'),
    (r'^get_fb_likes_list/(?P<call_type>[\w\.]+)/(?P<postfid>[\w\.]+)/$', 'get_fb_likes_list'),

    (r'^get_wall_chart/(?P<harvester_id>\d+)/(?P<userfid>[\w\.]+)/$', 'get_wall_chart'),
    (r'^get_otherwall_chart/(?P<harvester_id>\d+)/(?P<userfid>[\w\.]+)/$', 'get_otherwall_chart'),
    (r'^get_comment_chart/(?P<harvester_id>\d+)/(?P<userfid>[\w\.]+)/$', 'get_comment_chart'),
    (r'^get_commentpost_chart/(?P<harvester_id>\d+)/(?P<postfid>[\w\.]+)/$', 'get_commentpost_chart'),

    (r'^dwld_fb_posts_csv/', 'dwld_fb_posts_csv'),
    (r'^dwld_fb_comments_csv/', 'dwld_fb_comments_csv'),

    #DAILYMOTION
    (r'^dm/(?P<harvester_id>\d+)$', 'dm'),
    (r'^dm_user_detail/(?P<harvester_id>\d+)/fid/(?P<userfid>[\w\.]+)/$', 'dm_user_detail'),
    (r'^dm_video_detail/(?P<harvester_id>\d+)/(?P<videoid>[\w\.]+)/$', 'dm_video_detail'),
    #DAILYMOTION AJAX
    (r'^get_dm_list/(?P<call_type>[\w\.]+)/(?P<harvester_id>\d+)/$', 'get_dm_list'),
    (r'^get_dm_video_list/(?P<call_type>[\w\.]+)/(?P<userfid>[\w\.]+)/$', 'get_dm_video_list'),
    (r'^get_dm_fans_list/(?P<call_type>[\w\.]+)/(?P<userfid>[\w\.]+)/$', 'get_dm_fans_list'),
    (r'^get_dm_friends_list/(?P<call_type>[\w\.]+)/(?P<userfid>[\w\.]+)/$', 'get_dm_friends_list'),
    (r'^get_dm_following_list/(?P<call_type>[\w\.]+)/(?P<userfid>[\w\.]+)/$', 'get_dm_following_list'),
    (r'^get_dm_comment_list/(?P<call_type>[\w\.]+)/(?P<userfid>[\w\.]+)/$', 'get_dm_comment_list'),
    (r'^get_dm_videocomment_list/(?P<call_type>[\w\.]+)/(?P<videofid>[\w\.\*]+)/$', 'get_dm_videocomment_list'),

    (r'^get_dmvideo_chart/(?P<harvester_id>\d+)/(?P<userfid>[\w\.]+)/$', 'get_dmvideo_chart'),
    (r'^get_dmcomment_chart/(?P<harvester_id>\d+)/(?P<userfid>[\w\.]+)/$', 'get_dmcomment_chart'),
    (r'^get_dmvideocomment_chart/(?P<harvester_id>\d+)/(?P<videofid>[\w\.]+)/$', 'get_dmvideocomment_chart'),

    #YOUTUBE
    (r'^yt/(?P<harvester_id>\d+)$', 'yt'),
    (r'^yt_user_detail/(?P<harvester_id>\d+)/fid/(?P<userfid>.*)/$', 'yt_user_detail'),
    (r'^yt_video_detail/(?P<harvester_id>\d+)/(?P<videoid>.*)/$', 'yt_video_detail'),
    (r'^downloadytvideo/(?P<videoid>.*)/$', 'download_yt_video'),
    #YOUTUBE AJAX
    (r'^get_yt_list/(?P<call_type>[\w\.]+)/(?P<harvester_id>\d+)/$', 'get_yt_list'),
    (r'^get_yt_video_list/(?P<call_type>[\w\.]+)/(?P<userfid>.*)/$', 'get_yt_video_list'),
    (r'^get_yt_comment_list/(?P<call_type>[\w\.]+)/(?P<userfid>.*)/$', 'get_yt_comment_list'),
    (r'^get_yt_videocomment_list/(?P<call_type>[\w\.]+)/(?P<videofid>.*)/$', 'get_yt_videocomment_list'),

    (r'^get_ytvideo_chart/(?P<harvester_id>\d+)/fid/(?P<userfid>.*)/$', 'get_ytvideo_chart'),
    (r'^get_ytcomment_chart/(?P<harvester_id>\d+)/fid/(?P<userfid>.*)/$', 'get_ytcomment_chart'),
    (r'^get_ytvideocomment_chart/(?P<harvester_id>\d+)/fid/(?P<videofid>.*)/$', 'get_ytvideocomment_chart'),



    #(r'^$', 'index'),
    #(r'^reset_fb_token$', 'reset_fb_token'),
    #(r'^request_fb_token$', 'request_fb_token'),
    #(r'^test_fb_token$', 'test_fb_token'),

    #(r'^twitter_status/(?P<status_id>\d+)/$', 'twitter_status'),
    #(r'^twitter_search_detail/(?P<search_pmkid>\w+)/$', 'twitter_search_detail'),
    #(r'^twitter/(?P<harvester_id>\d+)/$', 'twitter'),

    #(r'^facebook_post/(?P<post_id>\w+)/$', 'facebook_post'),
    #(r'^facebook_detail/(?P<user_id>\d+)/$', 'facebook_detail'),
    #(r'^facebook/(?P<harvester_id>\d+)/$', 'facebook'),
    (r'^event_logs/$', 'get_event_logs'),
    (r'^event_logs/(?P<logfile>[\w.]+)$', 'get_event_logs'),


    (r'^api/1.0/(?P<command>[\w.]+)$', 'api_one_zero'),
)
