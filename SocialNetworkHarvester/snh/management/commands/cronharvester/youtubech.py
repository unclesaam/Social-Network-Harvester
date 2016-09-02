# coding=UTF-8

from datetime import timedelta
#import psutil
import time
import urllib
import json
import re
import os

from django.core.exceptions import ObjectDoesNotExist
from snh.models.youtubemodel import *
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
import snhlogger
from snh.utils import xml_formater
from snh.YoutubeV3Wrapper import YoutubeAPIClient
from apiclient.errors import HttpError

from settings import DEBUGCONTROL, MEDIA_ROOT, DOWNLOADED_VIDEO_PATH
debugging = DEBUGCONTROL['youtubech'], dLogger
if DEBUGCONTROL['youtubech']: print "DEBBUGING ENABLED IN %s"%__name__

logger = snhlogger.init_logger(__name__, "youtube.log")
logger.info(" "*500)


@dLogger.debug
def run_youtube_harvester():
    harvester_list = sort_harvesters_by_priority(YoutubeHarvester.objects.all())

    for harvester in harvester_list:
        harvester.harvest_in_progress = False
        harvester.save()

    try:
        for harvester in harvester_list:
            logger.info(u"The harvester %s is %s" % 
                                                    (unicode(harvester), 
                                                    "active" if harvester.is_active else "inactive"))
            try:
                pass
                #custom_migration(harvester)
                #set_comments_enabled(harvester)
                #test_getOrCreate(harvester)
            except:
                if debugging: dLogger.exception('AN ERROR HAS OCCURED:')

            if harvester.is_active:
                langs = ['en','fr',]
                params = {  'client_id': harvester.dev_key,
                        'caption_languages': langs
                    }
                client = YoutubeAPIClient(params)
                harvester.client = client
                run_harvester_v1(harvester)
    except:
        for harvester in harvester_list:
            harvester.harvest_in_progress = False
            harvester.save()
        raise

@dLogger.debug
def sort_harvesters_by_priority(all_harvesters):
    if debugging: dLogger.log("sort_harvesters_by_priority()")

    new_harvesters = [harv for harv in all_harvesters if harv.last_harvest_start_time == None]
    aborted_harvesters = [harv for harv in all_harvesters if harv.current_harvest_start_time != None and harv not in new_harvesters]
    clean_harvesters = [harv for harv in all_harvesters if harv not in aborted_harvesters and harv not in new_harvesters]
    
    sorted_harvester_list = new_harvesters
    sorted_harvester_list += sorted(clean_harvesters, key=lambda harvester: harvester.last_harvest_start_time)
    sorted_harvester_list += sorted(aborted_harvesters, key=lambda harvester: harvester.current_harvest_start_time)
    if debugging : dLogger.log('    sorted_harvester_list: %s'%sorted_harvester_list)
    return sorted_harvester_list

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

@dLogger.debug
def update_user(harvester, ytUser):
    if debugging: 
        dLogger.log("update_user()")
        #dLogger.pretty(ytUser)


    fid = ytUser['id']
    snh_user, new = YTUser.objects.get_or_create(fid=fid)

    if new: 
        logger.debug(u"New user created: %s", snh_user)
        if debugging: dLogger.log('    new user created: %s'%snh_user)
        snh_user.harvester = harvester
        snh_user.save()

    snh_user.update_from_youtube(ytUser)

@dLogger.debug
def update_users(harvester):
    if debugging: dLogger.log("update_users()")

    all_users = harvester.harvested_users.all()|harvester.ytusers_to_harvest.all()
    channelIdList = []

    for snhuser in all_users:
        if not snhuser.error_triggered:
            try:
                harvester.last_harvested_user = harvester.current_harvested_user
            except:
                harvester.last_harvested_user = None
            harvester.current_harvested_user = snhuser
            harvester.save()
            if snhuser.fid: 
                if re.search('[a-zA-Z]', snhuser.fid): # test if the fid has any alpha character. Otherwise it is a GPlus User (damn these...)
                    channelIdList.append(snhuser.fid)
            elif snhuser.username: 
                response = harvester.api_call('channel_lookup', {'userName': snhuser.username})
                #dLogger.pretty(response)
                if len(response[0]['items']) > 0:
                    snhuser.update_from_youtube(response[0]['items'][0])
        else:
            logger.info(u"Skipping user update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    subLists = [channelIdList[i:i+49] for i in range(0, len(channelIdList), 49)]
    for subList in subLists:
        stringList = ''
        for channelId in subList:
            stringList += channelId + ','
        try:
            response = harvester.api_call('channel_lookup',{'channelId':stringList})
            for ytUser in response[0]['items']:
                update_user(harvester, ytUser)
        except exception as e:
            time.sleep(1)
            dLogger.exception(e)
            if debugging: dLogger.log('    ERROR 500 received from youtube, retrying.')
            response = harvester.api_call('channel_lookup',{'channelId':stringList})
            for ytUser in response[0]['items']:
                update_user(harvester, ytUser)



    #usage = psutil.virtual_memory()
    logger.info(u"User harvest completed %s" % (harvester))


@dLogger.debug
def update_video(snhuser, ytvideo):
    if debugging: 
        dLogger.log("update_video()")
        #dLogger.pretty(ytvideo)

    fid = ytvideo['id']
    snhvideo = None
    try:
        try:
            snhvideo = YTVideo.objects.get(fid__exact=fid)
        except ObjectDoesNotExist:
            snhvideo = YTVideo(fid=fid, user=snhuser)
            snhvideo.save()
        snhvideo.update_from_youtube(snhuser, ytvideo)
    except:
        msg = u"Cannot update video %s" % (fid)
        logger.exception(msg)
        dLogger.exception(msg)
    return snhvideo

@dLogger.debug
def update_comment(harvester, comment, snhvideo, parentComment=None):
    if debugging:
        dLogger.log('update_comment()')
        #dLogger.pretty(comment)

    author_username = comment['snippet']['authorDisplayName']

    if 'authorChannelId' not in comment['snippet']: #shared on Google+ and the user has no Youtube Channel...
        userId = re.sub(r'.*/', '',comment['snippet']['authorChannelUrl'])
    else:
        userId = comment['snippet']['authorChannelId']['value']

    snhuser, new = YTUser.objects.get_or_create(fid=userId)
    if new:
        if debugging: dLogger.log('    New user created from comment: %s'%snhuser)
        snhuser.harvester = harvester
        snhuser.save()

    fid = comment['id']
    try:
        try:
            snhcomment = YTComment.objects.get(fid__exact=fid)
        except ObjectDoesNotExist:
            snhcomment = YTComment(fid=fid, video=snhvideo)
            snhcomment.save()
        if parentComment != None:
            snhcomment.parent_comment = parentComment
            snhcomment.save()
        snhcomment.update_from_youtube(snhvideo, snhuser, comment)            
    except:
        msg = u"Cannot update comment %s" % fid
        logger.exception(msg)
        if debugging: dLogger.exception(msg)
    return snhcomment


@dLogger.debug
def update_comment_thread(harvester, snhvideo, ytThread):
    if debugging: 
        dLogger.log("<YTComment: '%s'>::update_comment_thread()"%snhvideo)
        dLogger.log('    ytThread: ')
        #dLogger.pretty(ytThread)

    ytComment = ytThread['snippet']['topLevelComment']
    snhParentComment = update_comment(harvester, ytComment, snhvideo)

    if 'replies' in ytThread and snhParentComment:
        for reply in ytThread['replies']['comments']:
            update_comment(harvester, ytComment, snhvideo, snhParentComment)


    #usage = psutil.virtual_memory()
    logger.debug(u"Thread updated: comid:%s vidid:%s %s" % (snhParentComment.fid if snhParentComment else '',
            snhvideo.fid, harvester))

    return snhParentComment

@dLogger.debug
def update_all_comment_helper(harvester, snhvideo, comment_list):
    if debugging: dLogger.log("<YTVideo: '%s'>::update_all_comment_helper()"%snhvideo)
    for comment in comment_list[0]['items']:
        update_comment_thread(harvester, snhvideo, comment)
    if 'nextPageToken' in comment_list[0]:
        return comment_list[0]['nextPageToken']
    else:
        return None

@dLogger.debug
def update_all_comment(harvester,snhvideo):
    if debugging: dLogger.log("<YTVideo: '%s'>::update_all_comment()"%snhvideo)
    try:
        next_page_token = None
        try:
            comment_list = harvester.api_call("comment_threads_list",{"videoId":snhvideo.fid})
            next_page_token = update_all_comment_helper(harvester, snhvideo, comment_list)
        except Exception, e:
            if debugging: dLogger.log('    Error received from Youtube: %s'%e)
            snhvideo.comments_enabled = False
            snhvideo.save()
        while next_page_token:
            comment_list = harvester.api_call("comment_threads_list",{"videoId":snhvideo.fid, "pageToken":next_page_token})
            next_page_token = update_all_comment_helper(harvester, snhvideo, comment_list)

        #usage = psutil.virtual_memory()
        logger.info(u"Comment harvest completed for video: %s" % snhvideo)
    except HttpError as err:
        dLogger.exception(u"HttpError received for this video: %s (%s)" % (snhvideo.fid, err))
    except Exception as err:
        dLogger.exception(u"Unknown Error received for this video: %s (%s)" %(snhvideo.fid, err))


@dLogger.debug
def update_all_videos(harvester):
    if debugging: dLogger.log("update_all_videos()")

    all_users = harvester.ytusers_to_harvest.all()

    harvest_window_to = harvester.harvest_window_to.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    harvest_window_from = harvester.harvest_window_from.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    for snhuser in all_users:
        if not snhuser.error_triggered:
            logger.info(u"Will update user: %s(%s)" % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))
            nextPageToken = (True, None)
            videoId_list = []
            while nextPageToken[0]:
                activities_list = harvester.api_call("activities_list",
                                                    {"channelId":snhuser.fid, 
                                                    'pageToken':nextPageToken[1],
                                                    'parts':'id,contentDetails',
                                                    'publishedBefore':harvest_window_to,
                                                    'publishedAfter': harvest_window_from
                                                    })

                for item in activities_list['items']:
                    if 'contentDetails' in item and 'upload' in item['contentDetails']:
                        videoId_list.append(item['contentDetails']['upload']['videoId'])

                nextPageToken = (True, activities_list['nextPageToken']) if 'nextPageToken' in activities_list else (False, None)

            dLogger.log('    videoId_list: %s'%videoId_list)
            subLists = [videoId_list[i:i+49] for i in range(0, len(videoId_list), 49)]
            for subList in subLists:
                stringList = ''
                for videoId in subList:
                    stringList += videoId + ','
                
                response = harvester.api_call('video_list_lookup',{'videoIdList':stringList})
                #dLogger.pretty(response)
                for ytVideo in response['items']:
                    snhvideo = update_video(snhuser, ytVideo)
                    update_all_comment(harvester, snhvideo)
                    if harvester.download_videos and snhvideo.video_file_path == None:
                        download_video(harvester, snhvideo)
                        download_video_captions(harvester, snhvideo)

        else:
            logger.info(u"Skipping user update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    #usage = psutil.virtual_memory()
    logger.info(u"Video harvest completed %s" % (harvester))

@dLogger.debug
def download_video(harvester, snhVideo):
    if debugging: dLogger.log('download_video()')

    vid = harvester.api_call('video_download', {'videoId': snhVideo.fid})
    filename = '%syoutube_%s_%s.%s'%(DOWNLOADED_VIDEO_PATH,
        snhVideo.user.fid, snhVideo.fid, vid['ext'])
    if not os.path.isfile(filename):
        try:
            dwld = urllib.urlopen(vid['url']).read()
            video = open(filename, 'wb')
            video.write(dwld)
            video.close()
            snhVideo.video_file_path = filename
            snhVideo.save()
            logger.info('Video %s has been downloaded successfully'%snhVideo)
        except:
            dLogger.exception('Video download failed') 
            logger.info('Video download has failed')

@dLogger.debug
def download_video_captions(harvester, snhVideo):
    if debugging: dLogger.log('download_video_captions()')

    response = harvester.api_call('caption_list', {'videoId': snhVideo.fid})
    if response[0]:
        for lang in response[0]:
            filename = '%syoutube_%s_%s_%s.srt'%(DOWNLOADED_VIDEO_PATH,
                snhVideo.user.fid, snhVideo.fid, lang)
            snhCaption, new = YTVideoCaption.objects.get_or_create(srt_file_path=filename)
            if new:
                try:
                    dwld = urllib.urlopen(response[0][lang]).read()
                    caption = open(filename, 'wb')
                    caption.write(dwld)
                    caption.close()
                    snhCaption.language = lang
                    snhCaption.video = snhVideo
                    snhCaption.auto_generated = response[1]
                    snhCaption.save()
                    logger.info('%s caption have been downloaded successfully'%lang)
                except:
                    if debugging: dLogger.exception('Caption download failed')
                    logger.info('%s caption download has failed'%lang)

@dLogger.debug
def run_harvester_v1(harvester):
    if debugging: dLogger.log("run_harvester_v1()")
    harvester.start_new_harvest()
    try:

        start = time.time()
        update_users(harvester)
        update_all_videos(harvester)
        logger.info(u"Results computation complete in %ss" % (time.time() - start))

    except:
        logger.exception(u"EXCEPTION: %s" % harvester)
        dLogger.exception(u"EXCEPTION: %s" % harvester)
    finally:
        #usage = psutil.virtual_memory()
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))



def custom_migration(harvester):
    dLogger.log('custom_migration started')
    vids = YTVideo2.objects.all()
    for vid in vids:
        newVid = YTVideo.objects.create(user=vid.user,
            fid = vid.fid,
            url = vid.url,
            player_url = vid.player_url,
            swf_url = vid.swf_url,
            title = vid.title,
            published = vid.published,
            updated = vid.updated,
            recorded = vid.recorded,
            description = vid.description,
            category = vid.category,
            duration = vid.duration,
            favorite_count = vid.favorite_count,
            view_count = vid.view_count,
            like_count = vid.like_count,
            dislike_count = vid.dislike_count,
            comment_count = vid.comment_count,
            video_file_path = vid.video_file_path)
        dLogger.log('    newVid created: %s'%newVid)

def set_comments_enabled(harvester):
    all_vids = YTVideo.objects.filter(comments_enabled=False)
    for vid in all_vids:
        vid.comments_enabled = True
        vid.save()

def test_getOrCreate(harvester):
    user, new = YTUser.objects.get_or_create(fid='sadbhakjhdkhajgsjdhbaskgdfasbdjhgf')
    dLogger.log('harvester: %s'%harvester)
    dLogger.log('    user: %s'%user)
    dLogger.log('    new: %s'%new)