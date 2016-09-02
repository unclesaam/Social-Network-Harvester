# coding=UTF-8

from snh.models.twittermodel import *
from snh.models.facebookmodel import *
from snh.models.youtubemodel import *
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from settings import PROJECT_PATH, DEBUG
import os
from datetime import datetime
import snhlogger
import json
import sys
logger = snhlogger.init_logger(__name__, "view.log")

from settings import DEBUGCONTROL, dLogger
debugging = DEBUGCONTROL['apiviews']
if debugging: print "DEBBUGING ENABLED IN %s"%__name__


'''TODO:
record all api calls to a specific log
'''

## CREATE ##

def CreateTwitterHarvester(context):
    status = 'Not completed.'
    if 'aspira_pk' in context and context['aspira_pk'] != 0:
        harv = TwitterHarvester.objects.get(pk=context['aspira_pk'])
        status = 'Existing harvester modified.'
    else:
        try:
            harv = TwitterHarvester.objects.get(harvester_name=context['name'])
            status = 'Existing harvester modified.'
        except ObjectDoesNotExist:
            harv = TwitterHarvester()
            status = 'New harvester created.'
    for param in harv.api_params:
        if param in context:
            setattr(harv, harv.api_params[param], context[param])
    harv.save()
    response = {
        'command':'CreateTwitterHarvester',
        'status': status,
        'object':  harv.to_dict()
        }
    response['object']['aspira_pk'] = harv.pk
    return jsonResponse(response)

def CreateTwitterUserList(context):
    harv_id = context['tw_harvester_id']
    harv = TwitterHarvester.objects.get(pk=harv_id)
    user_id_list = []
    for user in context['tw_user_list']:
        try:
            newUser = TWUser.objects.get(screen_name=user['screen_name'])
        except ObjectDoesNotExist:
            newUser = TWUser.objects.create(screen_name=user['screen_name'])
        try:
            harv.twusers_to_harvest.get(screen_name=user['screen_name'])
        except ObjectDoesNotExist:
            harv.twusers_to_harvest.add(newUser)
        user_id_list.append(newUser.pk)
    harv.save()

    response = {
        'command':'CreateTwitterUserList',
        'status': 'completed',
        'harvester_id': harv.pk,
        'user_id_list': user_id_list,
        }
    return jsonResponse(response)

def CreateTwitterSearchList(context):
    harv_id = context['tw_harvester_id']
    harv = TwitterHarvester.objects.get(pk=harv_id)
    searchs_id_list = []
    for search in context['tw_search_list']:
        try:
            newSearch = TWSearch.objects.get(term=search['term'])
        except ObjectDoesNotExist:
            newSearch = TWSearch.objects.create(term=search['term'])
        harv.twsearch_to_harvest.add(newSearch)
        searchs_id_list.append(newSearch.pk)
    harv.save()

    response = {
        'command':'CreateTwitterSearchList',
        'status': 'completed',
        'harvester_id': harv.pk,
        'user_id_list': searchs_id_list,
        }
    return jsonResponse(response)

## GET ##

def getFormatedTweet(tweet, scope):
    dic = {}
    if len(scope) == 0:
        scope = ['pmk_id','user','fid','created_at','favorited',
        'retweet_count','retweeted','source','text','truncated',
        'text_urls','hash_tags','user_mentions','model_update_date','error_on_update',]
    for arg in scope:
        if hasattr(tweet, arg):
            attr = getattr(tweet, arg)
            if isinstance(attr, datetime):
                format = '%m %d %H:%M:%S +0000 %Y'
                attr = datetime.strftime(attr,format)
            elif arg == 'text_urls':
                attr = [a.original_url for a in attr.all()]
            elif arg == 'hash_tags':
                attr = [a.text for a in attr.all()]
            elif arg == 'user_mentions':
                attr = [a.screen_name for a in attr.all()]
            elif arg == 'user':
                attr = attr.screen_name
            dic[arg] = attr
        else:
            raise UnrecognizedAttribute('Tweet', arg)
    return dic


def GetTwitterTweetList(context):
    dLogger.pretty(context)
    data = []
    scope = []
    if 'scope' in context:
        scope = context['scope'][0].split(',')

    if 'harvester_name' in context:
        try:
            harv = TwitterHarvester.objects.get(harvester_name=context['harvester_name'][0])
        except ObjectDoesNotExist:
            return error('HarvesterDoesNotExistsError', 'No Twitter Harvester has been found for that name: %s'%context['harvester_name'][0], 'GetTwitterTweetList')
        for user in harv.twusers_to_harvest.all():
            tweetList = user.postedStatuses.all()
            try:
                data = {
                    'user_screen_name': user.screen_name,
                    'tweet_list': [getFormatedTweet(tweet, scope) for tweet in tweetList]
                }
            except UnrecognizedAttribute:
                return error('InvalidScopeArgument','One scope item for TWStatus is invalid','GetTwitterTweetList')

    elif 'user_screen_name' in context:
        try:
            user = TWUser.objects.get(screen_name=context['user_screen_name'][0])
        except ObjectDoesNotExist:
            return error('UserDoesNotExistsError', 'No Twitter User has been found for that name: %s'%context['screen_name'][0], 'GetTwitterTweetList')
        tweetList = user.postedStatuses.all()
        try:
            data = {
                'user_screen_name': user.screen_name,
                'tweet_list': [getFormatedTweet(tweet, scope) for tweet in tweetList]
            }
        except UnrecognizedAttribute:
            return error('InvalidScopeArgument','One scope item for TWStatus is invalid','GetTwitterTweetList')

    elif 'search_term' in context:
        return notImplementedError('GetTwitterHarvesterList (using search_term)')

    else:
        return InvalidRequestError('GetTwitterTweetList')


    response = {
        'data':data,
        'command':'CreateTwitterUserList',
        'status': 'completed',
    }
    return jsonResponse(response)

def GetTwitterHarvesterList(context):
    return notImplementedError('GetTwitterHarvesterList')

def GetTwitterUserList(context):
    return notImplementedError('GetTwitterUserList')

def GetTwitterSearchList(context):
    return notImplementedError('GetTwitterSearchList')

## Edit ##

def EditTwitterHarvester(context):
    return notImplementedError('EditTwitterHarvester')

def EditTwitterUser(context):
    return notImplementedError('EditTwitterUser')

def EditTwitterSearch(context):
    return notImplementedError('EditTwitterSearch')

## Delete ##

def DeleteTwitterHarvester(context):
    return notImplementedError('DeleteTwitterHarvester')

def DeleteTwitterUser(context):
    return notImplementedError('DeleteTwitterUser')

def DeleteTwitterSearch(context):
    return notImplementedError('DeleteTwitterSearch')


AVAILABLE_GET_COMMANDS = {
    'GetTwitterTweetList':          GetTwitterTweetList,
    'GetTwitterHarvesterList':      GetTwitterHarvesterList,
    'GetTwitterUserList':           GetTwitterUserList,
    'GetTwitterSearchList':         GetTwitterSearchList,
}

AVAILABLE_POST_COMMANDS = {
    'CreateTwitterHarvester':       CreateTwitterHarvester,
    'CreateTwitterUserList':        CreateTwitterUserList,
    'CreateTwitterSearchList':      CreateTwitterSearchList,
    'EditTwitterHarvester':         EditTwitterHarvester,
    'EditTwitterUser':              EditTwitterUser,
    'EditTwitterSearch':            EditTwitterSearch,
    'DeleteTwitterHarvester':       DeleteTwitterHarvester,
    'DeleteTwitterUser':            DeleteTwitterUser,
    'DeleteTwitterSearch':          DeleteTwitterSearch,
}

DEFAULT_OAUTH_KEY = "3685s6d7g9qh69i8s2bds54as7u3p2o4q7wdssj6dfsw6sc37uis3z6qw6s5dgb3ax25s6up3pout9753d"

def jsonResponse(dictObject): return HttpResponse(json.dumps(dictObject), content_type="application/json")

def authent(request): return jsonResponse({'oAuth_key': DEFAULT_OAUTH_KEY})

def error(errorType, errorValue, command): return jsonResponse({'error': {'type':errorType, 'value':errorValue}, 'command':command})
def notImplementedError(command): return error('notImplementedError', 'This method has not been implemented yet', command)
def InvalidRequestError(command): return error('InvalidRequestError', 'Invalid request', command)

@csrf_exempt
def api_one_zero(request, command):
    try:
        dLogger.log(command)
        if command == 'authent': return authent(request)
        elif 'oauth' in request.GET and request.GET['oauth'] == DEFAULT_OAUTH_KEY:
            return command_management(command, request)
        else:
            return error('UnauthentifiedError', 'You must use an authentification token to use AspirAPI', command)
    except Exception as e:
        dLogger.exception('Error occured in an API view')
        dLogger.log(request)
        return error('UnknownServerError', 'An error has occured while proceeding the request',command)

def command_management(command, request):
    if command in AVAILABLE_GET_COMMANDS:
        return AVAILABLE_GET_COMMANDS[command](dict(request.GET.iterlists()))
    elif command in AVAILABLE_POST_COMMANDS:
        return AVAILABLE_POST_COMMANDS[command](jsonLoader(request.POST))
    else:
        return InvalidRequestError(command)

def getHarvs(request):
    platform = request.GET['platform']
    harvs = {}
    if platform == 'tw':
        harvs['All data'] = '/tw/0'
        for harv in TwitterHarvester.objects.filter(is_active=True):
            harvs[harv.harvester_name] = '/tw/%s' % harv.pmk_id
    elif platform == 'fb':
        harvs['All data'] = '/fb/0'
        for harv in FacebookHarvester.objects.filter(is_active=True):
            harvs[harv.harvester_name] = '/fb/%s' % harv.pmk_id
    elif platform == 'yt':
        harvs['All data'] = '/yt/0'
        for harv in YoutubeHarvester.objects.filter(is_active=True):
            harvs[harv.harvester_name] = '/yt/%s' % harv.pmk_id
    return HttpResponse(json.dumps(harvs),content_type='application/json')


def jsonLoader(request):
    dictio = dict(request)
    key = dictio.keys()[0]
    #dLogger.log(key)
    #dLogger.log(len(key))
    j = json.loads(key)
    return j


class UnrecognizedAttribute(Exception):
    def __init__(self, paramName, objType):
        msg = 'The object %s has no attribute %s'%(objType, paramName)
        super(UnrecognizedAttribute,self).__init__(msg)
        self.exc_info = sys.exc_info()
















