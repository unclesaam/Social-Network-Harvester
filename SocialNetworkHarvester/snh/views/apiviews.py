# coding=UTF-8

from snh.models.twittermodel import *
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from settings import PROJECT_PATH, DEBUG
import os
import snhlogger
import json
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

@csrf_exempt
def api_one_zero(request, command):
    try:
        dLogger.log(command)
        if command == 'authent': return authent(request)
        elif 'oauth' in request.GET and request.GET['oauth'] == DEFAULT_OAUTH_KEY:
            return command_management(command, request)
        else:
            return error('UnauthentifiedError', 'You must use an authentification token to use AspirAPI')
    except Exception as e:
        dLogger.exception('Error occured in an API view')
        dLogger.log(request)
        return error('UnknownServerError', 'An error has occured while proceeding the request',command)

def command_management(command, request):
    if command in AVAILABLE_GET_COMMANDS:
        return AVAILABLE_GET_COMMANDS[command](json.loads(dict(request.GET).keys()[0]))
    elif command in AVAILABLE_POST_COMMANDS:
        return AVAILABLE_POST_COMMANDS[command](jsonLoader(request.POST))
    else:
        return error('InvalidRequestError', 'Invalid request')



def jsonLoader(request):
    dictio = dict(request)
    key = dictio.keys()[0]
    #dLogger.log(key)
    #dLogger.log(len(key))
    j = json.loads(key)
    return j



















