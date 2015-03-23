# coding=UTF-8

import twitter
import time
import datetime
import urllib

from twython import *
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from snh.models.twittermodel import *

import snhlogger
import os


#########################################################
debugging = 1
if debugging: 
    print "DEBBUGING ENABLED IN %s"%__name__
    debugLogger = snhlogger.init_custom_logger('debug'+__name__, "debugLogger.log", '%(message)s')
    debugLogger.info("            "*200)
#########################################################

logger = snhlogger.init_logger(__name__, "twitter.log")

def run_twitter_harvester():
    harvester_list = TwitterHarvester.objects.all()

    for harvester in harvester_list:
        harvester.update_client_stats()
        logger.info(u"The harvester %s is %s" % 
                                                (unicode(harvester), 
                                                "active" if harvester.is_active else "inactive"))
        if harvester.is_active and not harvester.remaining_hits > 0:
            logger.warning(u"The harvester %s is %s but has exceeded the rate limit. Need to wait? %s" % 
                                                (unicode(harvester), 
                                                "active" if harvester.is_active else "inactive", 
                                                harvester.get_stats()))

        if harvester.is_active and harvester.remaining_hits > 0:
            run_harvester_v2(harvester)

        if harvester.is_active:        
            run_harvester_search(harvester)

def get_latest_statuses_page(harvester, user, page):
    if debugging: debugLogger.info( "twitterch::get_latest_statuses_page(harvester: %s, user: %s, page: %s)"%(harvester, user.screen_name, page))

    since_max = [u"since_id", None]
    if user.was_aborted and user.last_harvested_status:
        since_max = [u"max_id",user.last_harvested_status.fid]
        
    latest_statuses_page = harvester.api_call("GetUserTimeline",
                                                {
                                                u"screen_name":unicode(user.screen_name), 
                                                since_max[0]:since_max[1], 
                                                #u"include_rts":True, 
                                                #u"include_entities":True,
                                                u"count":100,
                                                #u"page":page,
                                                })
    return latest_statuses_page

def sleeper(retry_count):
    if debugging: debugLogger.info( "twitterch::sleeper(retry_count: %s)"%retry_count)
    retry_delay = 1
    wait_delay = retry_count*retry_delay
    wait_delay = 60 if wait_delay > 60 else wait_delay
    time.sleep(wait_delay)

def manage_exception(retry_count, harvester, user, page):
    if debugging: debugLogger.info( "twitterch::manage_exception(retry_count: %s, harvester: %s, user: %s, page: %s)"%(retry_count, harvester, user, page))
    msg = u"Exception for the harvester %s for %s at page %d. Retry:%d" % (harvester, unicode(user), page, retry_count)
    logger.exception(msg)
    retry_count += 1
    return (retry_count, retry_count > harvester.max_retry_on_fail)

def manage_twitter_exception(retry_count, harvester, user, page, tex):
    if debugging: debugLogger.info( "twitterch::manage_twitter_exception(retry_count: %s, harvester: %s, user: %s, page: %s, tex: %s)"%(retry_count, 
                                                                harvester, user.screen_name, page, type(tex)))

    retry_count += 1
    need_a_break = retry_count > harvester.max_retry_on_fail

    if unicode(tex) == u"Not found":
        user.error_triggered = True
        user.save()
        need_a_break = True
        msg = u"Exception for the harvester %s for %s at page %d. Retry:%d. The user does not exists!" % (harvester, unicode(user), page, retry_count)
        logger.exception(msg)
    elif unicode(tex) == u"Capacity Error":
        logger.debug(u"%s:%s:%d. Capacity Error. Retrying." % (harvester, unicode(user), page))
    elif unicode(tex).startswith(u"Rate limit exceeded"):
        harvester.update_client_stats()
        msg = u"Exception for the harvester %s for %s at page %d. Retry:%d." % (harvester, unicode(user), page, retry_count)
        logger.exception(msg)
        raise
    elif unicode(tex) == u"{u'error': u'Invalid query'}" or unicode(tex) == u"Invalid query":
        logger.debug(u"%s:%s:%d. Invalid query. Breaking." % (harvester, unicode(user), page))
        need_a_break = True
    else:
        print tex
        msg = u"Exception for the harvester %s for %s at page %d. Retry:%d. %s" % (harvester, unicode(user), page, retry_count, tex)
        logger.exception(msg)

    return (retry_count, need_a_break)

def get_latest_statuses(harvester, user):
    if debugging: debugLogger.info( "twitterch::get_latest_statuses(harvester: %s, user: %s)"%(harvester, user.screen_name))

    page = 1
    retry = 0
    lsp = []
    latest_statuses = []
    too_old = False

    try:
        logger.debug(u"%s:%s(%d):%d" % (harvester, unicode(user), user.fid if user.fid else 0, page))
        lsp = get_latest_statuses_page(harvester, user, page)
        if len(lsp) != 0:
            for status in lsp:
                status_time = datetime.strptime(status.created_at,'%a %b %d %H:%M:%S +0000 %Y')
                if status_time > harvester.harvest_window_from and \
                        status_time < harvester.harvest_window_to:
                    update_user_status(status, user)

        page += 1
    except twitter.TwitterError, tex:
        (retry, need_a_break) = manage_twitter_exception(retry, harvester, user, page, tex)
        if need_a_break:
            return latest_statuses
        else:
            sleeper(retry)             
    except:
        (retry, need_a_break) = manage_exception(retry, harvester, user, page)
        if need_a_break:
            return latest_statuses
        else:
            sleeper(retry)  

    return latest_statuses

def update_user_status(status, user):
    if debugging: debugLogger.info( "twitterch::update_user_status(status: '%s...', user: %s)"%(status.text[:60], user.screen_name))
    try:
        tw_status = TWStatus.objects.get(fid__exact=status.id)
    except ObjectDoesNotExist:
        tw_status = TWStatus(user=user)
        tw_status.save()
        #if debugging: debugLogger.info( "New <TWStatus> created('%s...')"%(tw_status))
    tw_status.update_from_twitter(status,user)
    user.last_harvested_status = tw_status
    user.save()

def get_existing_user(param):
    if debugging: debugLogger.info( "twitterch::get_existing_user(param: %s)"%(param))
    user = None
    try:
        user = TWUser.objects.get(**param)
    except MultipleObjectsReturned:
        user = TWUser.objects.filter(**param)[0]
        logger.warning(u"Duplicated user in DB! %s, %s" % (user, user.fid))
    except ObjectDoesNotExist:
        pass
    return user

def status_from_search(harvester, tw_status):
    if debugging: debugLogger.info( "twitterch::status_from_search(harvester: %s, tw_status: %s)"%(harvester, tw_status))
    user = None
    snh_status = None
    twUser = tw_status.user
    try:
        user = get_existing_user({"fid__exact":twUser.id})
        if not user:
            user = get_existing_user({"screen_name__exact":twUser.screen_name})        
        if not user:
            user = TWUser(
                            fid=twUser.id,
                            screen_name=twUser.screen_name,
                         )
            user.save()
            logger.info(u"New user created in status_from_search! %s", user)

        try:
            snh_status = TWStatus.objects.get(fid__exact=tw_status.id)
        except ObjectDoesNotExist:
            snh_status = TWStatus(
                                    fid=tw_status.id,
                                    user=user,
                                    )
            snh_status.save()
        snh_status.update_from_rawtwitter(tw_status, user)
    except:
        msg = u"Cannot update status %s for user %s:%s)" % (tw_status.id, twUser.screen_name, twUser.id)
        logger.exception(msg) 

    return snh_status

def update_search(snh_search, snh_status):
    if debugging: debugLogger.info( "twitterch::update_search(snh_search: %s, snh_status: %s)"%(snh_search, snh_status))

    if snh_status and snh_search.status_list.filter(fid__exact=snh_status.fid).count() == 0:
        snh_search.status_list.add(snh_status)
        snh_search.latest_status_harvested = snh_status
        snh_search.save()

def call_search(harvester, term, page, since_id=None):
    if debugging: debugLogger.info( "twitterch::call_search(harvester: %s, term: %s, page: %s)"%(harvester, term, page))
    retry = 0
    status_list = None
    next_page = False
    while status_list is None and harvester.remaining_hits > 0:
        try:
            uniterm = urllib.urlencode({"k":term.encode('utf-8')}).split("=")[1:][0]
            params = {   
                        u"term":uniterm, 
                        u"since_id":since_id, 
                        u"count": 10,
                        "include_entities":"True"
                        }
            logger.info(u"Getting new page:%d retry:%d, params:%s" % (page,retry,params))
            data = harvester.api_call(u"GetSearch", params)
            harvester.remaining_hits -= 1
            if data != []:
                status_list = data

        except twitter.TwitterError, tex:
            (retry, need_a_break) = manage_twitter_exception(retry, harvester, term, page, tex)
            if need_a_break:
                status_list = []
            else:
                sleeper(retry)

    if not status_list:
        status_list = []

    logger.info(u"Next page for %s: %s Hits to go: %d, len:%d" % (term, harvester, harvester.remaining_hits,len(status_list)))
    return status_list, next_page

def search_term(harvester, twsearch):
    if debugging: debugLogger.info( "twitterch::search_term(harvester: %s, twsearch: %s)"%(harvester, twsearch))

    page = 1
    too_old = False
    since_id = None
    if twsearch.latest_status_harvested is not None:
        since_id = unicode(twsearch.latest_status_harvested.fid)
    status_list, next_page = call_search(harvester, twsearch.term, page, since_id)
    while status_list and not too_old:
        page += 1
        for status in status_list:

            status_time = datetime.strptime(status["created_at"],'%a, %d %b %Y %H:%M:%S +0000')
            if status_time > harvester.harvest_window_from and \
                    status_time < harvester.harvest_window_to:

                snh_status = status_from_search(harvester, status)
                update_search(twsearch, snh_status)

            if status_time < harvester.harvest_window_from or not next_page:
                too_old = True
                break
        logger.info(u"last status date: %s" % status_time)
        if next_page:
            status_list, next_page = call_search(harvester, twsearch.term, page, since_id)

def para_search_term(harvester, all_twsearch):
    if debugging: debugLogger.info( "twitterch::para_search_term(harvester: %s, all_twsearch: %s)"%(harvester, all_twsearch))
    
    searches = []
    for twsearch in all_twsearch:
        since_id = None
        if twsearch.latest_status_harvested is not None:
            since_id = unicode(twsearch.latest_status_harvested.fid)
        searches.append({
                            "twsearch":twsearch,
                            "page":1,
                            "has_more":True,
                            "since_id":since_id,
                        })
    new_page_in_the_box = True

    while new_page_in_the_box:
        new_page_in_the_box = False

        for search in searches:
            if search["has_more"]:
                new_page_in_the_box = True

                logger.info(u"Will search for %s at page %d, since_id:%s" % (search["twsearch"].term, search["page"], search["since_id"]))
                status_list, has_more = call_search(harvester, search["twsearch"].term, search["page"], search["since_id"])

                search["page"] += 1
                search["has_more"] = has_more

                status_time = None
                for status in status_list:

                    status_time = datetime.strptime(status.created_at,'%a %b %d %H:%M:%S +0000 %Y')
                    if status_time > harvester.harvest_window_from and \
                            status_time < harvester.harvest_window_to:

                        snh_status = status_from_search(harvester, status)
                        update_search(search["twsearch"], snh_status)

                    if status_time < harvester.harvest_window_from:
                        search["has_more"] = False
                        break

                if status_time is None or len(status_list) == 0:
                    search["has_more"] = False
                 
                logger.info(u"last status date: %s" % status_time)


def update_user_twython(twuser, user):
    if debugging: debugLogger.info( "twitterch::update_user_twython(twuser: %s, user: %s)"%(twuser['screen_name'], user))
    try:
        user.update_from_rawtwitter(twuser,twython=True)
    except:
        msg = u"Cannot update user info for %s:(%d)" % (unicode(twuser), user.fid if user.fid else 0)
        logger.exception(msg)       

def update_users_twython(harvester):
    if debugging: debugLogger.info( "twitterch::update_users_twython(harvester: %s)"%harvester)
    all_users = harvester.twusers_to_harvest.all()
    screen_names = []
    user_screen_name = {}

    for user in all_users:
        screen_names.append(user.screen_name)
        user_screen_name[user.screen_name.upper()] = user

    step_size = 100
    split_screen_names = [screen_names[i:i+step_size] for i  in range(0, len(screen_names), step_size)]
    tt = harvester.get_tt_client()
    for screen_names in split_screen_names:
        nameList = screen_names[0]
        for screenName in screen_names[1:]:
            nameList+=',%s'%screenName
        twuser_list_page = tt.lookup_user(screen_name=nameList)
        for twuser in twuser_list_page:
            screen_name = twuser["screen_name"].upper()
            user = user_screen_name[screen_name]
            update_user_twython(twuser, user)

def run_harvester_v2(harvester):
    if debugging: debugLogger.info( "twitterch::run_harvester_v2(harvester: %s)"%(harvester))

    harvester.start_new_harvest()
    logger.info(u"START REST: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
    try:
        if True:
            update_users_twython(harvester)

        if True:
            user = harvester.get_next_user_to_harvest()
            while user and harvester.remaining_hits > 0:
                if not user.error_triggered:
                    logger.info(u"Start: %s:%s(%d). Hits to go: %d" % (harvester, unicode(user), user.fid if user.fid else 0, harvester.remaining_hits))
                    get_latest_statuses(harvester, user)
                else:
                    logger.info(u"Skipping: %s:%s(%d) because user has triggered the error flag." % (harvester, unicode(user), user.fid if user.fid else 0))

                user.was_aborted = False
                user.save()
                user = harvester.get_next_user_to_harvest()

    except twitter.TwitterError:
        harvester.update_client_stats()
    finally:
        harvester.end_current_harvest()
        if harvester.last_user_harvest_was_aborted:
            aborted_user = harvester.get_current_harvested_user()
            aborted_user.was_aborted = True
            aborted_user.save()
    
    logger.info(u"End REST: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))

def run_harvester_search(harvester):
    if debugging: debugLogger.info ("twitterch::run_harvester_search(harvester: %s)"%(harvester))
            
    if True:
        harvester.start_new_harvest()
        logger.info(u"START SEARCH API: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
        try:
            all_twsearch = harvester.twsearch_to_harvest.all()
            para_search_term(harvester, all_twsearch)
        except twitter.TwitterError, e:
            msg = u"ERROR for %s" % twsearch.term
            logger.exception(msg)    
        finally:
            harvester.end_current_harvest()
            logger.info(u"End SEARCH API: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
        
    logger.info(u"End: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))


