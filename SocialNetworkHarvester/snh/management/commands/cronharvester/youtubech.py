# coding=UTF-8

from datetime import timedelta
import psutil
import time
import urllib

from django.core.exceptions import ObjectDoesNotExist
from snh.models.youtubemodel import *
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
import snhlogger
from snh.utils import xml_formater

from gdata.youtube.client import RequestError, YouTubeError

#########################################################
debugging = 1
if debugging: 
    print "DEBBUGING ENABLED IN %s"%__name__
    debugLogger = snhlogger.init_custom_logger('debug'+__name__, "debugLogger.log", '(%(filename)-15s) %(message)s')
#########################################################

logger = snhlogger.init_logger(__name__, "youtube.log")
logger.info(" "*500)

def run_youtube_harvester():
    harvester_list = YoutubeHarvester.objects.all()
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

def get_existing_user(param):
    user = None
    try:
        user = YTUser.objects.get(**param)
    except MultipleObjectsReturned:
        user = YTUser.objects.filter(**param)[0]
        logger.warning(u"Duplicated user in DB! %s, %s" % (user, user.fid))
    except ObjectDoesNotExist:
        pass
    return user

def update_user(harvester, userid):
    if debugging: debugLogger.info("<'%s'>::update_user()", userid)
    snh_user = None

    try:
        uniuserid = urllib.urlencode({"k":userid.encode('utf-8')}).split("=")[1:][0]
        ytuser = harvester.api_call("GetYouTubeUserEntry",{"username":uniuserid})
        split_uri = ytuser.id.text.split("/")
        fid = split_uri[len(split_uri)-1]
        title = ytuser.title.text.encode('utf-8', 'ignore')

        snh_user = get_existing_user({"fid__exact":fid})
        if not snh_user:
            snh_user = get_existing_user({"username__exact":userid})
        if not snh_user:
            snh_user = YTUser(
                            fid=fid,
                            username=userid,
                            title=title,
                         )
            snh_user.save()
            logger.info(u"New user created in status_from_search! %s", snh_user)
        snh_user.update_from_youtube(ytuser)
    except gdata.service.RequestError, e:

        if debugging: debugLogger.info("    error received: %s", e)

        msg = u"RequestError on user %s. Trying to update anyway" % (userid)
        logger.info(msg)
        if e[0]["status"] == 403 or e[0]["status"] == 400:
            snh_user = get_existing_user({"username__exact":userid})
            if not snh_user:
                snh_user = YTUser(
                                username=userid,
                             )
                snh_user.save()
                logger.info(u"New user created in status_from_search! %s", snh_user)
        else:
            msg = u"RequestError on user %s!!! Force update failed!!!" % (userid)
            logger.exception(msg)
    except:
        msg = u"Cannot update user %s" % (userid)
        logger.exception(msg)
    return snh_user

def update_users(harvester):
    if debugging: debugLogger.info("update_users()")

    all_users = harvester.ytusers_to_harvest.all()

    for snhuser in all_users:
        if not snhuser.error_triggered:
            uid = snhuser.fid if snhuser.fid else snhuser.username
            update_user(harvester, uid)
        else:
            logger.info(u"Skipping user update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    usage = psutil.virtual_memory()
    logger.info(u"User harvest completed %s Mem:%s MB" % (harvester, int(usage[4])/(1024.0)))

def update_video(snhuser, ytvideo):
    if debugging: debugLogger.info("<'%s'>::update_video()", ytvideo.title.text)
    split_uri = ytvideo.id.text.split("/")
    fid = split_uri[len(split_uri)-1] 
    snhvideo = None
    try:
        try:
            snhvideo = YTVideo.objects.get(fid__exact=fid)
        except ObjectDoesNotExist:
            snhvideo = YTVideo(fid=fid, user=snhuser)
            snhvideo.save()
        snhvideo.update_from_youtube(snhuser, ytvideo)            
    except:
        msg = u"Cannot update video %s" % (unicode(ytvideo.id.text,'UTF-8'))
        logger.exception(msg)
    return snhvideo

def update_comment(harvester, snhvideo, ytcomment):
    if debugging: debugLogger.info("<'%s'>::update_comment()", snhvideo)
    author = ytcomment.author[0]
    author_fid = author.uri.text.split('/')[-1]
    snhuser = update_user(harvester, author_fid)
    split_uri = ytcomment.id.text.split("/")
    fid = split_uri[-1]
    try:
        try:
            snhcomment = YTComment.objects.get(fid__exact=fid)
        except ObjectDoesNotExist:
            snhcomment = YTComment(fid=fid, video=snhvideo)
            snhcomment.save()
        snhcomment.update_from_youtube(snhvideo, snhuser, ytcomment)            
    except:
        msg = u"Cannot update comment %s" % (unicode(ytcomment.id.text,'UTF-8'))
        logger.exception(msg)

    usage = psutil.virtual_memory()
    logger.debug(u"Commment updated: comid:%s vidid:%s %s Mem:%s MB" % (snhcomment.fid,snhvideo.fid, harvester, int(usage[4])/(1024.0)))

    return snhcomment

def update_all_comment_helper(harvester, snhvideo, comment_list):
    if debugging: debugLogger.info("<'%s'>::update_all_comment_helper()", snhvideo)
    for comment in comment_list.entry:
        #if debugging: debugLogger.info('    comment to update: <"%s">'%str(comment.author))
        update_comment(harvester, snhvideo, comment)
    
    get_next_comment_uri = comment_list.GetNextLink().href if comment_list.GetNextLink() else None
    return get_next_comment_uri

def update_all_comment(harvester,snhvideo):
    if debugging: debugLogger.info("<'%s'>::update_all_comment()", snhvideo)
    try:
        comment_list = harvester.api_call("GetYouTubeVideoCommentFeed",{"video_id":snhvideo.fid})
        get_next_comment_uri = update_all_comment_helper(harvester, snhvideo, comment_list)
        while get_next_comment_uri:
            comment_list = harvester.api_call("GetYouTubeVideoCommentFeed",{"uri":get_next_comment_uri})
            get_next_comment_uri = update_all_comment_helper(harvester, snhvideo, comment_list)

        usage = psutil.virtual_memory()
        logger.info(u"    Comment harvest completed for this video: %s %s Mem:%s MB" % (snhvideo.fid, harvester,int(usage[4])/(1024.0)))
    except YouTubeError as err:
        debugLogger.info(u"    YouTubeError received for this video: %s (%s)" % (snhvideo.fid, err))
    except RequestError as err:
        debugLogger.info(u"    RequestError received for this video: %s (%s)" % (snhvideo.fid, err))
    except Exception as err:
        debugLogger.info(u"    Unknown Error received for this video: %s (%s)" %(snhvideo.fid, err))



def update_all_videos(harvester):
    if debugging: debugLogger.info("update_all_videos()")
    all_users = harvester.ytusers_to_harvest.all()

    for snhuser in all_users:
        out_of_window = False
        if not snhuser.error_triggered:
            logger.info(u"Will update user: %s(%s)" % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))
            get_vid_url = 'http://gdata.youtube.com/feeds/api/users/%s/uploads?' % snhuser.username
            while get_vid_url and not out_of_window:
                video_list = harvester.api_call("GetYouTubeVideoFeed",{"uri":get_vid_url})
                for video in video_list.entry:
                    published = datetime.strptime(video.published.text,'%Y-%m-%dT%H:%M:%S.000Z')
                    if published < harvester.harvest_window_to:
                        snhvideo = update_video(snhuser, video)
                        update_all_comment(harvester, snhvideo)

                    if published < harvester.harvest_window_from:
                        out_of_window = True
                        break
                if not out_of_window:
                    get_vid_url = video_list.GetNextLink().href if video_list.GetNextLink() else None
        else:
            logger.info(u"Skipping user update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    usage = psutil.virtual_memory()
    logger.info(u"Video harvest completed %s Mem:%s MB" % (harvester, int(usage[4])/(1024.0)))

def run_harvester_v1(harvester):
    if debugging: debugLogger.info("run_harvester_v1()")
    harvester.start_new_harvest()
    try:

        start = time.time()
        update_users(harvester)
        update_all_videos(harvester)
        logger.info(u"Results computation complete in %ss" % (time.time() - start))

    except:
        logger.exception(u"EXCEPTION: %s" % harvester)
    finally:
        usage = psutil.virtual_memory()
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s Mem:%s MB" % (harvester,unicode(harvester.get_stats()),int(usage[4])/(1024.0)))

