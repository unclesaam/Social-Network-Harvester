# coding=UTF-8

from datetime import timedelta
import resource
import time

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from snh.models.dailymotionmodel import *

import snhlogger
logger = snhlogger.init_logger(__name__, "dailymotion.log")

from settings import DEBUGCONTROL
debugging = DEBUGCONTROL['dailymotionch']
if DEBUGCONTROL['dailymotionch']: 
    print "DEBBUGING ENABLED IN %s"%__name__
    debugLogger = snhlogger.init_custom_logger('debug'+__name__, "debugLogger.log", '(%(filename)-17s) %(message)s')

def run_dailymotion_harvester():
    harvester_list = DailyMotionHarvester.objects.all()
    for harvester in harvester_list:
        logger.info(u"The harvester %s is %s" % 
                                                (unicode(harvester), 
                                                "active" if harvester.is_active else "inactive"))
        if harvester.is_active:
            run_harvester_v1(harvester)

def sleeper(retry_count):
    retry_delay = 1
    wait_delay = retry_count*retry_delay
    wait_delay = 10 if wait_delay > 10 else wait_delay
    time.sleep(wait_delay)

def get_timedelta(dm_time):
    ts = datetime.strptime(dm_time,'%Y-%m-%dT%H:%M:%S+0000')
    return (datetime.utcnow() - ts).days

def get_comment_paging(page):
    __after_id = None
    new_page = False
    if u"paging" in page and u"next" in page[u"paging"]:
        url = urlparse.parse_qs(page[u"paging"][u"next"])
        __after_id = url[u"__after_id"][0]
        new_page = True
    return ["__after_id",__after_id], new_page

def update_user(harvester, userid=None, username=None):

    reqid = userid if userid else username
    result = harvester.api_call("GET",
                                str(
                                    "/user/%(username)s?fields="
                                    "id,"
                                    "type,"
                                    "status,"
                                    "username,"
                                    "screenname,"
                                    #"fullname," #access_required
                                    "created_time,"
                                    "description,"
                                    "language,"
                                    "gender,"
                                    #"email," #access_required
                                    #"birthday," #access_required
                                    #"ip," #access_required
                                    #"useragent," #access_required
                                    "views_total,"
                                    "videos_total,"
                                    #"cloudkey," #access_required
                                    "url,"
                                    "avatar_small_url,"
                                    "avatar_medium_url,"
                                    "avatar_large_url,"
                                    "tile,"
                                    "tile.id,"
                                    "tile.video,"
                                    "tile.type,"
                                    "tile.title,"
                                    "tile.summary,"
                                    "tile.mode,"
                                    "tile.icon_url,"
                                    "tile.icon2x_url,"
                                    "tile.thumbnail_url,"
                                    "tile.thumbnail2x_url,"
                                    "tile.views_total,"
                                    "tile.videos_total,"
                                    "tile.context,"
                                    "tile.explicit,"
                                    "tile.sorts,"
                                    "tile.sorts_labels,"
                                    "tile.sorts_default,"
                                    "tile.filters,"
                                    "tile.filters_labels,"
                                    "tile.filters_default,"
                                    "tile.new_items,"
                                    "videostar,"
                                    "videostar.id,"
                                    "videostar.title,"
                                    "videostar.tags,"
                                    "videostar.tag,"
                                    "videostar.channel,"
                                    "videostar.description,"
                                    "videostar.language,"
                                    "videostar.country,"
                                    "videostar.url,"
                                    "videostar.tiny_url,"
                                    "videostar.created_time,"
                                    "videostar.modified_time,"
                                    "videostar.taken_time,"
                                    "videostar.status,"
                                    "videostar.encoding_progress,"
                                    "videostar.type,"
                                    "videostar.paywall,"
                                    "videostar.rental_price,"
                                    "videostar.rental_price_formatted,"
                                    "videostar.rental_duration,"
                                    "videostar.mode,"
                                    "videostar.onair,"
                                    "videostar.live_publish_url,"
                                    #"videostar.audience_url," #access_required
                                    #"videostar.ads," #access_required
                                    "videostar.private,"
                                    "videostar.explicit,"
                                    "videostar.published,"
                                    "videostar.duration,"
                                    "videostar.allow_comments,"
                                    "videostar.owner,"
                                    "videostar.user,"
                                    "videostar.owner_screenname,"
                                    "videostar.owner_username,"
                                    "videostar.owner_fullname,"
                                    "videostar.owner_url,"
                                    "videostar.owner_avatar_small_url,"
                                    "videostar.owner_avatar_medium_url,"
                                    "videostar.owner_avatar_large_url,"
                                    "videostar.thumbnail_url,"
                                    "videostar.thumbnail_small_url,"
                                    "videostar.thumbnail_medium_url,"
                                    "videostar.thumbnail_large_url,"
                                    "videostar.rating,"
                                    "videostar.ratings_total,"
                                    "videostar.views_total,"
                                    "videostar.views_last_hour,"
                                    "videostar.views_last_day,"
                                    "videostar.views_last_week,"
                                    "videostar.views_last_month,"
                                    "videostar.comments_total,"
                                    "videostar.bookmarks_total,"
                                    "videostar.embed_html,"
                                    "videostar.embed_url,"
                                    "videostar.swf_url,"
                                    "videostar.aspect_ratio,"
                                    #"videostar.log_view_url," #access_required
                                    #"videostar.log_external_view_url," #access_required
                                    #"videostar.log_view_urls," #access_required
                                    #"videostar.log_external_view_urls," #access_required
                                    "videostar.upc,"
                                    "videostar.isrc,"
                                    #"videostar.stream_h264_ld_url," #access_required
                                    #"videostar.stream_3gp_url," #access_required
                                    #"videostar.stream_h264_url," #access_required
                                    #"videostar.stream_h264_hq_url," #access_required
                                    #"videostar.stream_h264_hd_url," #access_required
                                    #"videostar.stream_h264_hd1080_url," #access_required
                                    #"videostar.stream_h264_ld_rtmpe_url," #access_required
                                    #"videostar.stream_3gp_rtmpe_url," #access_required
                                    #"videostar.stream_h264_rtmpe_url," #access_required
                                    #"videostar.stream_h264_hq_rtmpe_url," #access_required
                                    #"videostar.stream_h264_hd_rtmpe_url," #access_required
                                    #"videostar.stream_h264_hd1080_rtmpe_url," #access_required
                                    #"videostar.stream_live_hls_url," #access_required
                                    #"videostar.stream_live_rtmp_url," #access_required
                                    #"videostar.stream_live_rtsp_url," #access_required
                                    #"videostar.publish_date," #access_required
                                    #"videostar.expiry_date," #access_required
                                    "videostar.geoblocking,"
                                    "videostar.3d"
                                    "" %
                                    {
                                        "username":reqid,
                                    })
                                )

    dmuser = result["result"]
    snh_user = None
    try:
        if userid:
            snh_user = get_existing_user({"fid__exact":userid})
        elif username:
            snh_user = get_existing_user({"username__exact":username})
        if not snh_user:
            snh_user = DMUser(
                            fid=dmuser["id"],
                            username=dmuser["username"],
                         )
            snh_user.save()
            logger.debug(u"New user created in status_from_search! %s", snh_user)

        snh_user.update_from_dailymotion(dmuser)
    except:
        msg = u"Cannot update user %s" % (dmuser)
        logger.exception(msg) 

    return snh_user

def get_existing_user(param):
    user = None
    try:
        user = DMUser.objects.get(**param)
    except MultipleObjectsReturned:
        user = DMUser.objects.filter(**param)[0]
        logger.warning(u"Duplicated user in DB! %s, %s" % (user, user.fid))
    except ObjectDoesNotExist:
        pass
    return user

def update_users(harvester):

    all_users = harvester.dmusers_to_harvest.all()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    logger.info(u"Will harvest users for %s Mem:%s MB" % (harvester,unicode(getattr(usage, "ru_maxrss")/(1024.0))))

    for snhuser in all_users:
        if not snhuser.error_triggered:
            update_user(harvester,username=snhuser.username)
        else:
            logger.info(u"Skipping user update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))


def update_users_friends_fans(harvester):

    all_users = harvester.dmusers_to_harvest.all()

    usage = resource.getrusage(resource.RUSAGE_SELF)
    logger.info(u"Will harvest users fans, friends and following. %s Mem:%s MB" % (harvester,unicode(getattr(usage, "ru_maxrss")/(1024.0))))

    for snhuser in all_users:
        if not snhuser.error_triggered:
            update_user_fans(harvester, snhuser)
            update_user_friends(harvester, snhuser)
            update_user_following(harvester, snhuser)
        else:
            logger.info(u"Skipping user update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))


def update_user_fans(harvester, snhuser):

    has_more = True
    page = 0
    while has_more:
        page += 1
        result = harvester.api_call("GET",
                                    str(
                                        "/user/%(username)s/fans?page=%(page)d&limit=%(limit)d&fields="
                                        "id,"
                                        "type,"
                                        "status,"
                                        "username,"
                                        "screenname,"
                                        #"fullname," #access_required
                                        "created_time,"
                                        "description,"
                                        "language,"
                                        "gender,"
                                        #"email," #access_required
                                        #"birthday," #access_required
                                        #"ip," #access_required
                                        #"useragent," #access_required
                                        "views_total,"
                                        "videos_total,"
                                        #"cloudkey," #access_required
                                        "url,"
                                        "avatar_small_url,"
                                        "avatar_medium_url,"
                                        "avatar_large_url"
                                        "" %
                                        {
                                            "username":snhuser.username,
                                            "page":page,
                                            "limit":100,
                                        })
                                    )

        for i in result["result"]["list"]:
            logger.debug(u"---------fans:%s" % i["id"])
            snhuser.update_fan_from_dailymotion(i)

        has_more = result["result"]["has_more"]


def update_user_friends(harvester, snhuser):

    has_more = True
    page = 0
    while has_more:
        page += 1
        result = harvester.api_call("GET",
                                    str(
                                        "/user/%(username)s/friends?page=%(page)d&limit=%(limit)d&fields="
                                        "id,"
                                        "type,"
                                        "status,"
                                        "username,"
                                        "screenname,"
                                        #"fullname," #access_required
                                        "created_time,"
                                        "description,"
                                        "language,"
                                        "gender,"
                                        #"email," #access_required
                                        #"birthday," #access_required
                                        #"ip," #access_required
                                        #"useragent," #access_required
                                        "views_total,"
                                        "videos_total,"
                                        #"cloudkey," #access_required
                                        "url,"
                                        "avatar_small_url,"
                                        "avatar_medium_url,"
                                        "avatar_large_url"
                                        "" %
                                        {
                                            "username":snhuser.username,
                                            "page":page,
                                            "limit":100,
                                        })
                                    )

        for i in result["result"]["list"]:
            logger.debug(u"---------friends:%s" % i["id"])
            snhuser.update_friend_from_dailymotion(i)

        has_more = result["result"]["has_more"]

def update_user_following(harvester, snhuser):

    has_more = True
    page = 0
    while has_more:
        page += 1
        result = harvester.api_call("GET",
                                    str(
                                        "/user/%(username)s/following?page=%(page)d&limit=%(limit)d&fields="
                                        "id,"
                                        "type,"
                                        "status,"
                                        "username,"
                                        "screenname,"
                                        #"fullname," #access_required
                                        "created_time,"
                                        "description,"
                                        "language,"
                                        "gender,"
                                        #"email," #access_required
                                        #"birthday," #access_required
                                        #"ip," #access_required
                                        #"useragent," #access_required
                                        "views_total,"
                                        "videos_total,"
                                        #"cloudkey," #access_required
                                        "url,"
                                        "avatar_small_url,"
                                        "avatar_medium_url,"
                                        "avatar_large_url"
                                        "" %
                                        {
                                            "username":snhuser.username,
                                            "page":page,
                                            "limit":100,
                                        })
                                    )

        for i in result["result"]["list"]:
            logger.debug(u"---------following:%s" % i["id"])
            snhuser.update_friend_from_dailymotion(i)

        has_more = result["result"]["has_more"]


def get_video(harvester, videoid):
    result = harvester.api_call("GET",
                                str(
                                    "/video/%(id)s?fields="
                                    "id,"
                                    "title,"
                                    "tags,"
                                    "tag,"
                                    "channel,"
                                    "channel.id,"
                                    "channel.name,"
                                    "channel.description,"
                                    "channel.tile,"
                                    "description,"
                                    "language,"
                                    "country,"
                                    "url,"
                                    "tiny_url,"
                                    "created_time,"
                                    "modified_time,"
                                    "taken_time,"
                                    "status,"
                                    "encoding_progress,"
                                    "type,"
                                    "paywall,"
                                    "rental_price,"
                                    "rental_price_formatted,"
                                    "rental_duration,"
                                    "mode,"
                                    "onair,"
                                    "live_publish_url,"
                                    #"audience_url," #access_required
                                    #"ads," #access_required
                                    "private,"
                                    "explicit,"
                                    "published,"
                                    "duration,"
                                    "allow_comments,"
                                    "owner,"
                                    "user,"
                                    #"owner.id,"
                                    #"owner.type,"
                                    #"owner.status,"
                                    #"owner.username,"
                                    #"owner.screenname,"
                                    #"owner.fullname,"
                                    #"owner.created_time,"
                                    #"owner.description,"
                                    #"owner.language,"
                                    #"owner.gender,"
                                    #"owner.email,"
                                    #"owner.birthday,"
                                    #"owner.ip,"
                                    #"owner.useragent,"
                                    #"owner.views_total,"
                                    #"owner.videos_total,"
                                    #"owner.cloudkey,"
                                    #"owner.url,"
                                    #"owner.avatar_small_url,"
                                    #"owner.avatar_medium_url,"
                                    #"owner.avatar_large_url,"
                                    #"owner.tile,"
                                    #"owner.videostar,"
                                    #"owner_screenname,"
                                    #"owner_username,"
                                    #"owner_fullname,"
                                    #"owner_url,"
                                    #"owner_avatar_small_url,"
                                    #"owner_avatar_medium_url,"
                                    #"owner_avatar_large_url,"
                                    "thumbnail_url,"
                                    "thumbnail_small_url,"
                                    "thumbnail_medium_url,"
                                    "thumbnail_large_url,"
                                    "rating,"
                                    "ratings_total,"
                                    "views_total,"
                                    "views_last_hour,"
                                    "views_last_day,"
                                    "views_last_week,"
                                    "views_last_month,"
                                    "comments_total,"
                                    "bookmarks_total,"
                                    "embed_html,"
                                    "embed_url,"
                                    "swf_url,"
                                    "aspect_ratio,"
                                    #"log_view_url," #access_required
                                    #"log_external_view_url," #access_required
                                    #"log_view_urls," #access_required
                                    #"log_external_view_urls," #access_required
                                    "upc,"
                                    "isrc,"
                                    #"stream_h264_ld_url," #access_required
                                    #"stream_3gp_url," #access_required
                                    #"stream_h264_url," #access_required
                                    #"stream_h264_hq_url," #access_required
                                    #"stream_h264_hd_url," #access_required
                                    #"stream_h264_hd1080_url," #access_required
                                    #"stream_h264_ld_rtmpe_url," #access_required
                                    #"stream_3gp_rtmpe_url," #access_required
                                    #"stream_h264_rtmpe_url," #access_required
                                    #"stream_h264_hq_rtmpe_url," #access_required
                                    #"stream_h264_hd_rtmpe_url," #access_required
                                    #"stream_h264_hd1080_rtmpe_url," #access_required
                                    #"stream_live_hls_url," #access_required
                                    #"stream_live_rtmp_url," #access_required
                                    #"stream_live_rtsp_url," #access_required
                                    #"publish_date," #access_required
                                    #"expiry_date," #access_required
                                    "geoblocking,"
                                    "3d" %
                                        {
                                        "id":videoid,
                                        }
                                    )
                                )
    dmvideo = result["result"]
    return dmvideo

def update_video(harvester, snhuser, dmvideo):

    try:
        try:
            snh_video = DMVideo.objects.get(fid__exact=dmvideo["id"])
        except ObjectDoesNotExist:
            snh_video = DMVideo(user=snhuser)
            snh_video.save()
        snh_video.update_from_dailymotion(snhuser, dmvideo)                
    except:
        msg = u"Cannot update video %s" % (dmvideo["id"])
        logger.exception(msg) 

    return snh_video

def update_all_comments(harvester, snhvideo):

    has_more = True
    page = 0
    while has_more:
        page += 1
        result = harvester.api_call("GET",
                                    str(
                                        "/video/%(id)s/comments?page=%(page)d&limit=%(limit)d" %
                                            {
                                            "id":snhvideo.fid,
                                            "page":page,
                                            "limit":100,
                                            }
                                        )
                                    )
        for i in result["result"]["list"]:
            logger.debug(u"---------comment:%s" % i["id"])
            snh_comment = update_comment(harvester,snhvideo,i["id"])
        has_more = result["result"]["has_more"]
        logger.debug(u"---------comment page:%d" % page)


def update_comment(harvester, snhvideo, dmcommentid):
    result = harvester.api_call("GET",
                                str(
                                    "/comment/%(id)s?fields="
                                    "id,"
                                    "created_time,"
                                    "message,"
                                    "language,"
                                    "locked,"
                                    "owner,"
                                    "owner.id,"
                                    "owner.type,"
                                    "owner.status,"
                                    "owner.username,"
                                    "owner.screenname,"
                                    "owner.created_time,"
                                    "owner.description,"
                                    "owner.language,"
                                    "owner.gender,"
                                    "owner.views_total,"
                                    "owner.videos_total,"
                                    "owner.url,"
                                    "owner.avatar_small_url,"
                                    "owner.avatar_medium_url,"
                                    "owner.avatar_large_url,"
                                    "owner.tile,"
                                    "owner.videostar"
                                    "" %
                                        {
                                        "id":dmcommentid,
                                        }
                                    )
                                )
    dmcomment = result["result"]
    snh_user = update_user(harvester, dmcomment["owner.id"])
    snh_comment = None
    try:
        try:
            snh_comment = DMComment.objects.get(fid__exact=dmcomment["id"])
        except ObjectDoesNotExist:
            snh_comment = DMComment(video=snhvideo)
            snh_comment.save()
        snh_comment.update_from_dailymotion(snhvideo, snh_user, dmcomment)                
    except:
        msg = u"Cannot update comment %s" % (dmcomment["id"])
        logger.exception(msg) 

    return snh_comment


def update_all_videos(harvester):

    all_users = harvester.dmusers_to_harvest.all()
    video_list = []
    for snhuser in all_users:
        if not snhuser.error_triggered:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            logger.info(u"Will harvest %s video for %s Mem:%s MB" % (snhuser.screenname, harvester,unicode(getattr(usage, "ru_maxrss")/(1024.0))))
            has_more = True
            page = 0
            out_of_window = False
            while has_more and not out_of_window:
                page += 1
                result = harvester.api_call("GET",
                                            str(
                                                "/user/%(username)s/videos?page=%(page)d&limit=%(limit)d" %
                                                    {
                                                    "username":snhuser.username,
                                                    "page":page,
                                                    "limit":100,
                                                    }
                                                )
                                            )
                for i in result["result"]["list"]:

                    dmvideo = get_video(harvester, i["id"])
                    published =  datetime.fromtimestamp(float(dmvideo["created_time"]))
                    if published < harvester.harvest_window_to:
                        snh_video = update_video(harvester,snhuser,dmvideo)
                        update_all_comments(harvester, snh_video)

                    if published < harvester.harvest_window_from:
                        out_of_window = True
                        break

                has_more = result["result"]["has_more"]
        else:
            logger.info(u"Skipping user update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))


def run_harvester_v1(harvester):
    harvester.start_new_harvest()
    try:
        start = time.time()
        update_users(harvester)
        update_users_friends_fans(harvester)
        update_all_videos(harvester)
        logger.info(u"Results computation complete in %ss" % (time.time() - start))

    except:
        logger.exception(u"EXCEPTION: %s" % harvester)
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s Mem:%s MB" % (harvester,unicode(harvester.get_stats()),unicode(getattr(usage, "ru_maxrss")/(1024.0))))

