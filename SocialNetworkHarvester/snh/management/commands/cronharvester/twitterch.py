# coding=UTF-8

import twitter
import time
import datetime
import urllib
import urllib2
import json
from bs4 import BeautifulSoup as bs

from twython import *
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from snh.models.twittermodel import *


import snhlogger
import os


from settings import DEBUGCONTROL, dLogger
debugging = DEBUGCONTROL['twitterch']
if debugging: print "DEBBUGING ENABLED IN %s"%__name__

import requests
from requests_oauthlib import OAuth1
requests.packages.urllib3.disable_warnings()

logger = snhlogger.init_logger(__name__, "twitter.log")

@dLogger.debug
def run_twitter_harvester():
    if debugging: dLogger.log( "run_twitter_harvester()")

    #custom_export()

    harvester_list = TwitterHarvester.objects.all()
    for harvester in harvester_list:
        logger.info(u"The harvester %s is %s" % 
                    (unicode(harvester), 
                    "active" if harvester.is_active else "inactive"))


        if harvester.is_active:    
            harvester.start_new_harvest()

            harvester.update_client_stats()
            if harvester.remaining_user_timeline_hits <= 0 and harvester.remaining_user_lookup_hits <= 0:
                warn = u"The harvester %s has exceeded the status rate limits. Need to wait? %s" % (unicode(harvester), harvester.get_stats())
                logger.warning(warn)
            else:
                run_harvester_timeline(harvester)
                harvester.update_client_stats()
            
            if harvester.remaining_search_hits <= 0:
                warn = u"The harvester %s has exceeded the search rate limit. Need to wait? %s" % (unicode(harvester), harvester.get_stats())
                logger.warning(warn)
            else:
                run_harvester_search(harvester)
                harvester.update_client_stats()
            
            if harvester.remaining_user_lookup_hits <= 0:
                warn = u"The harvester %s has exceeded the user lookup rate limit. Need to wait? %s" % (unicode(harvester), harvester.get_stats())
                logger.warning(warn)
            else:
                run_users_update(harvester)
                harvester.update_client_stats()

            harvester.end_current_harvest()
    if debugging: dLogger.log('Harvest has ended for all harvesters')



@dLogger.debug
def get_latest_statuses_page(harvester, user):
    if debugging: dLogger.log("get_latest_statuses_page(harvester: %s, user: %s)"%(harvester, user.screen_name.encode('utf-8')))

    
    if user.last_harvested_status:
        since_max = [u"max_id",user.last_harvested_status.fid-1]

    elif user.last_valid_status_fid: #dernier status posté dans la plage du harvester (ou le plus ancien trouvé)
        since_max = [u"max_id",int(user.last_valid_status_fid)-1]

    else:
        since_max = [u"since_id", None]
        
    latest_statuses_page = harvester.api_call("GetUserTimeline",
        {   u"screen_name":unicode(user.screen_name), 
            since_max[0]:since_max[1], 
            u"count":200})
    harvester.remaining_user_timeline_hits -= 1
    harvester.save()
    return latest_statuses_page

@dLogger.debug
def sleeper(retry_count):
    if debugging: dLogger.log( "sleeper(retry_count: %s)"%retry_count)
    retry_delay = 1
    wait_delay = retry_count*retry_delay
    wait_delay = 60 if wait_delay > 60 else wait_delay
    time.sleep(wait_delay)

@dLogger.debug
def manage_exception(retry_count, harvester, user):
    if debugging: dLogger.log( "manage_exception(retry_count: %s, harvester: %s, user: %s)"%(retry_count, harvester, user))
    msg = u"Exception for the harvester %s for %s. Retry:%d" % (harvester, unicode(user), retry_count)
    logger.exception(msg)
    if debugging: dLogger.exception(msg)
    retry_count += 1
    return (retry_count, retry_count > harvester.max_retry_on_fail)

@dLogger.debug
def manage_twitter_exception(retry_count, harvester, user, tex):
    if debugging: dLogger.log( "manage_twitter_exception()")

    retry_count += 1
    need_a_break = retry_count > harvester.max_retry_on_fail

    if unicode(tex) == u"Not found":
        user.error_triggered = True
        user.save()
        need_a_break = True
        msg = u"Exception for the harvester %s for %s. Retry:%d. The user does not exists!" % (harvester, unicode(user), retry_count)
        logger.exception(msg)
        if debugging: dLogger.exception(msg)
    elif unicode(tex) == u"Capacity Error":
        logger.debug(u"%s:%s. Capacity Error. Retrying." % (harvester, unicode(user)))
    elif unicode(tex).startswith(u"Rate limit exceeded"):
        harvester.update_client_stats()
        msg = u"Exception for the harvester %s for %s. Retry:%d." % (harvester, unicode(user), retry_count)
        logger.exception(msg)
        if debugging: dLogger.exception(msg)
        raise
    elif unicode(tex) == u"{u'error': u'Invalid query'}" or unicode(tex) == u"Invalid query":
        logger.debug(u"%s:%s. Invalid query. Breaking." % (harvester, unicode(user)))
        need_a_break = True
    else:
        print tex
        msg = u"Exception for the harvester %s for %s. Retry:%d. %s" % (harvester, unicode(user), retry_count, tex)
        logger.exception(msg)
        if debugging: dLogger.exception(msg)

    return (retry_count, need_a_break)

@dLogger.debug
def get_latest_statuses(harvester, user):
    if debugging: dLogger.log( "get_latest_statuses(harvester: %s, user: %s)"%(harvester, user.screen_name.encode('utf-8')))

    retry = 0
    lsp = []
    latest_statuses = []
    too_old = False
    too_recent = True

    try:
        logger.debug(u"%s:%s(%d)" % (harvester, unicode(user), user.fid if user.fid else 0))
        lsp = get_latest_statuses_page(harvester, user)
        #if debugging: dLogger.log( "    latest status page:%s"%lsp)
        if len(lsp) != 0:
            for status in lsp:
                status_time = datetime.strptime(status.created_at,'%a %b %d %H:%M:%S +0000 %Y')

                if status_time < harvester.harvest_window_to:
                    too_recent = False
                    if status_time > harvester.harvest_window_from:
                        update_user_status(status, user, harvester.keep_raw_statuses)
                    else:
                        too_old = True
                        if debugging: dLogger.log( "    Tweet trop vieux! date: %s"%(status_time))
                        break
                else:
                    if debugging: dLogger.log( "    Tweet trop recent! date: %s"%(status_time))
                    user.last_valid_status_fid = status.id

        if too_old or len(lsp) == 0: # will start over from the most recent (valid) status
            user.last_harvested_status = None
            user.save()

        elif too_recent:
            harvester.haverst_deque.append(user) #will continue with this one until we reach the right timing

    except twitter.TwitterError, tex:
        (retry, need_a_break) = manage_twitter_exception(retry, harvester, user, tex)
        if need_a_break:
            return latest_statuses
        else:
            sleeper(retry)             
    except:
        (retry, need_a_break) = manage_exception(retry, harvester, user)
        if need_a_break:
            return latest_statuses
        else:
            sleeper(retry)  

    return latest_statuses

@dLogger.debug
def update_user_status(status, user,keepRaw):
    #if debugging: dLogger.log( "update_user_status(status: '%s...', user: %s)"%(status.text[:60], user.screen_name))
    try:
        tw_status = TWStatus.objects.get(fid__exact=status.id)
    except ObjectDoesNotExist:
        tw_status = TWStatus(user=user)
        tw_status.save()
        if debugging: dLogger.log( "    New <TWStatus> created('%s...')"%(tw_status))
    tw_status.update_from_twitter(status,user,keepRaw)
    user.last_harvested_status = tw_status
    user.save()

@dLogger.debug
def get_existing_user(param):
    #if debugging: dLogger.log( "get_existing_user()")
    user = None
    try:
        user = TWUser.objects.get(**param)
    except MultipleObjectsReturned:
        user = TWUser.objects.filter(**param)[0]
        logger.warning(u"Duplicated user in DB! %s, %s" % (user, user.fid))
    except ObjectDoesNotExist:
        pass
    #if debugging: dLogger.log( "   user found: %s"%user)
    return user

@dLogger.debug
def update_search(snh_search, snh_status):
    #if debugging: dLogger.log( "update_search(snh_search: %s, snh_status: %s)"%(snh_search, snh_status))

    if snh_status and snh_search.status_list.filter(fid__exact=snh_status.fid).count() == 0:
        snh_search.status_list.add(snh_status)
        snh_search.save()

@dLogger.debug
def search_all_terms(harvester, snh_searches):
    if debugging: dLogger.log( "search_all_terms()")
    logger.info(u"Will search for %s," % [search.term.encode('utf-8', 'ignore') for search in snh_searches])
    
    searches = [snh_search for snh_search in snh_searches]

    while len(searches) > 0 and harvester.remaining_search_hits > 0:
        snh_search = searches.pop(0)
        status_id_list = search_term(harvester, snh_search)

        if status_id_list:
            searches.append(snh_search) 
            update_statuses(harvester, snh_search, status_id_list)
        else:
            # finished the harvest for that term. starting over next time
            dLogger.log('    %s HAS FINISHED!'%snh_search)
            snh_search.latest_status_harvested = None 
            snh_search.save()

@dLogger.debug
def search_term(harvester, snh_search):
    if debugging: dLogger.log( "search_term()")

    new_statuses_list = []
    last_harvested_status = snh_search.latest_status_harvested

    max_id = None
    if last_harvested_status:
        max_id = int(last_harvested_status.fid) -1
        dLogger.log('    Latest statuse harvested date: %s'%last_harvested_status.created_at)

    while len(new_statuses_list) < 80:
        status_id_list = collect_tweets_from_html(harvester, snh_search, max_id)

        if len(status_id_list) > 0:
            new_statuses_list += status_id_list
            max_id = int(status_id_list[-1]) - 1
        else: 
            break

    if len(new_statuses_list) == 0:
        return None
    return new_statuses_list

@dLogger.debug
def update_statuses(harvester, snh_search, status_id_list):
    if debugging: 
        dLogger.log('update_statuses()')
        dLogger.log('    snh_search: %s'%snh_search)
        dLogger.log('    status_id_list: %s'%status_id_list)

    statuses_ids = status_id_list[0]
    for status_id in status_id_list[1:]:
        statuses_ids += ',%s'%status_id
    #dLogger.log('    statuses_ids: %s'%statuses_ids)
    statuses = api_statuses_lookup(harvester, statuses_ids, include_entities=True)

    for tw_status in sorted(statuses,key=lambda x:x['created_at'], reverse=True):
        #dLogger.log(tw_status['created_at'])

        tw_user = tw_status['user']
        snh_user, new = TWUser.objects.get_or_create(screen_name=tw_user['screen_name'])
        if new: 
            try:
                dLogger.log('    new user created: %s'%snh_user)
            except:
                dLogger.pretty(tw_status)
                raise

            snh_user.harvester = harvester
            snh_user.save()

        snh_status, new = TWStatus.objects.get_or_create(fid=tw_status['id_str'],
                                                user=snh_user)
        if new: dLogger.log('    new status created: %s'%snh_status)

        try:
            snh_status.update_from_rawtwitter(tw_status, snh_user, harvester.keep_raw_statuses)
            update_search(snh_search, snh_status)
        except Exception as e:
            if debugging: dLogger.exception(e)
            logger.exception('AN ERROR HAS OCCURED WHILE SAVING TWEET TO DB:')
    snh_search.latest_status_harvested = snh_status
    snh_search.save()


@dLogger.debug
def api_statuses_lookup(harvester, ids, include_entities=False):
    if debugging: 
        dLogger.log('api_statuses_lookup()')
        #dLogger.log('    ids: %s'%ids)

    url = 'https://api.twitter.com/1.1/statuses/lookup.json?id=%s'%ids
    if include_entities:
        url += '&include_entities=1'

    auth = OAuth1(harvester.consumer_key, 
        harvester.consumer_secret,
        harvester.access_token_key, 
        harvester.access_token_secret)

    response = []
    try:
        response = requests.get(url,auth=auth).json()
        harvester.remaining_search_hits -= 1
        harvester.save()
    except Exception as e:
        dLogger.exception(e)

    return response

@dLogger.debug
def collect_tweets_from_html(harvester,snh_search,max_id=None):
    if debugging: 
        dLogger.log('collect_tweets_from_html()')
        #dLogger.log('    snh_search: %s'%snh_search)
        #dLogger.log('    max_id: %s'%max_id)

    since = datetime.strftime(harvester.harvest_window_from, '%Y-%m-%d')
    until = datetime.strftime(harvester.harvest_window_to, '%Y-%m-%d')

    query = snh_search.term.encode('utf-8')
    params = '%s #%s since:%s until:%s'%(query,query,since,until)
    if max_id: params += ' max_id:%s'%max_id
    safe_url = 'https://twitter.com/search?q=' + urllib.quote(params)

    dLogger.log('    URL: %s'%safe_url)
    try:
        data = urllib2.urlopen(safe_url)
    except:
        time.sleep(1)
        data = urllib2.urlopen(safe_url)
    page = bs(data, "html.parser")
    tweetBox = page.find('ol', id='stream-items-id')
    tweets = tweetBox.findAll('li')
    status_id_list = []
    for tweet in tweets:
        if tweet.has_attr('data-item-id'):
            status_id_list.append(tweet['data-item-id'])
    return status_id_list

@dLogger.debug
def update_user_batch(harvester, user_batch):
    if debugging: dLogger.log( "update_user_batch(%d items)"%(len(user_batch) if user_batch else 0))
    userList = []
    userObjects = {}
    try:
        for user in user_batch:
            userList.append(user.screen_name)
            userObjects[user.screen_name.lower()] = user

        twModels = harvester.api_call('UsersLookup', {
                        'screen_name': userList, 
                        'include_entities': True
                    })
        harvester.remaining_user_lookup_hits -= 1
        harvester.save()

        for twModel in twModels:
            try:
                userObjects[twModel.screen_name.lower()].update_from_twitter(twModel)
            except:
                if debugging: dLogger.exception("ERROR UPDATING FROM TWITTER: %s"%twModel.screen_name.lower())
    except:
        if debugging: dLogger.exception( "ERROR WHILE UPDATING USER BATCH:")


@dLogger.debug
def run_harvester_timeline(harvester):
    if debugging: dLogger.log( "run_harvester_timeline(harvester: %s)"%(harvester))

    logger.info(u"START REST: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))

    try:
        user = harvester.get_next_user_to_harvest()

        while user and harvester.remaining_user_timeline_hits > 0:

            if not user.harvester:
                user.harvester = harvester
                user.save()

            if not user.error_triggered:

                logger.info(u"Start: %s:%s(%d). Hits to go: %d" % (harvester, unicode(user), user.fid if user.fid else 0, harvester.remaining_user_timeline_hits))
                get_latest_statuses(harvester, user)
            else:
                logger.info(u"Skipping: %s:%s(%d) because user has triggered the error flag." % (harvester, unicode(user), user.fid if user.fid else 0))

            user.was_aborted = False
            user.save()
            user = harvester.get_next_user_to_harvest()

    except twitter.TwitterError:
        harvester.update_client_stats()

    finally:
        if harvester.last_user_harvest_was_aborted and harvester.get_current_harvested_user():
            aborted_user = harvester.get_current_harvested_user()
            aborted_user.was_aborted = True
            aborted_user.save()
    
    logger.info(u"End REST: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))

@dLogger.debug
def run_harvester_search(harvester):
    if debugging: dLogger.log ("run_harvester_search(harvester: %s)"%(harvester))
            
    logger.info(u"START SEARCH API: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
    try:
        all_twsearch = harvester.twsearch_to_harvest.all()
        search_all_terms(harvester, all_twsearch)
    except twitter.TwitterError, e:
        msg = u"ERROR for %s" % twsearch.term
        logger.exception(msg)    
        if debugging: dLogger.exception(msg)
    finally:
        logger.info(u"End SEARCH API: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
        
    logger.info(u"End: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))


@dLogger.debug
def run_users_update(harvester):
    if debugging: dLogger.log ("run_users_update(harvester: %s)"%(harvester))

    logger.info(u"START user update: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
    while harvester.remaining_user_lookup_hits > 0:
        logger.info(u"New user batch to update. User lookup hits to go: %s" %(harvester.remaining_user_lookup_hits))
        user_batch = harvester.get_next_user_batch_to_update()
        if user_batch:
            update_user_batch(harvester, user_batch)
        else:
            break
    logger.info(u"End user update for %s Stats:%s" % (harvester,unicode(harvester.get_stats())))


def custom_migration():
    params = [  
            'harvester_type',
            'client',
            'tt_client',
            'consumer_key',
            'consumer_secret',
            'access_token_key',
            'access_token_secret',
            'remaining_search_hits',
            'remaining_user_timeline_hits',
            'remaining_user_lookup_hits',
            'reset_time_in_seconds',
            'hourly_limit',
            'reset_time',
            #'twusers_to_harvest',
            #'twsearch_to_harvest',
            'last_harvested_user',
            'current_harvested_user',
            'last_updated_user',
            'current_updated_user',
            ]
    for harv2 in TwitterHarvester2.objects.all():
        harv = TwitterHarvester.objects.create()
        for param in params:
            dLogger.log('param: %s'%param)
            setattr(harv, param, getattr(harv2, param))
        harv.save()
        dLogger.log('copied %s'%harv)
        
def custom_export():
    harv = TwitterHarvester.objects.get(pk=4)
    harv.update_client_stats()
    dLogger.log(harv.get_client().GetRateLimitStatus('statuses')['resources']['statuses']['/statuses/lookup'])


    open("C:\Users\Sam\Desktop\\abvote.json", 'w').close()
    f = open("C:\Users\Sam\Desktop\\abvote.json", 'w')

    hashtag = TWSearch.objects.get(pk=31)
    statuses = hashtag.status_list.all()
    ids = [status.fid for status in statuses]

    for twid in ids:
        data = harv.api_call('GetStatus', {'id':twid, 'include_entities': 'False'})
        js = json.dumps(data.AsDict(), ensure_ascii=False)
        f.write(js.encode('utf-8', 'ignore'))
    f.close()







