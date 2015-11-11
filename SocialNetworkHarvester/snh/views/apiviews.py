# coding=UTF-8

from snh.models.twittermodel import *

from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect, HttpResponse
from settings import PROJECT_PATH, DEBUG
import os
import snhlogger
import json
logger = snhlogger.init_logger(__name__, "view.log")

from settings import DEBUGCONTROL, dLogger
debugging = DEBUGCONTROL['apiviews']
if debugging: print "DEBBUGING ENABLED IN %s"%__name__


'''TODO:
record all api calls to a designed log
'''

## CREATE ##
@dLogger.debug
def CreateTwitterHarvester(context):
    dLogger.log('context: %s'%context)
    try:
        harv = TwitterHarvester()
        for param in harv.api_params:
            if param in context:
                setattr(harv, harv.api_params[param], context[param])
        harv.save()

        return jsonResponse({
            'request':'CreateTwitterHarvester',
            'status': 'completed',
            'object':  harv.to_dict()
            })
    except:
        dLogger.exception('API ERROR')

def CreateTwitterUserList(context):
    return error('notImplementedError', 'This method has not been implemented yet')

def CreateTwitterSearchList(context):
    return error('notImplementedError', 'This method has not been implemented yet')

## GET ##
def GetTwitterHarvesterList(context):
    return error('notImplementedError', 'This method has not been implemented yet')

def GetTwitterUserList(context):
    return error('notImplementedError', 'This method has not been implemented yet')

def GetTwitterSearchList(context):
    return error('notImplementedError', 'This method has not been implemented yet')

## Edit ##
def EditTwitterHarvester(context):
    return error('notImplementedError', 'This method has not been implemented yet')

def EditTwitterUser(context):
    return error('notImplementedError', 'This method has not been implemented yet')

def EditTwitterSearch(context):
    return error('notImplementedError', 'This method has not been implemented yet')

## Delete ##
def DeleteTwitterHarvester(context):
    return error('notImplementedError', 'This method has not been implemented yet')

def DeleteTwitterUser(context):
    return error('notImplementedError', 'This method has not been implemented yet')

def DeleteTwitterSearch(context):
    return error('notImplementedError', 'This method has not been implemented yet')


AVAILABLE_COMMANDS = {
    'CreateTwitterHarvester':       CreateTwitterHarvester,
    'CreateTwitterUserList':        CreateTwitterUserList,
    'CreateTwitterSearchList':      CreateTwitterSearchList,
    'GetTwitterHarvesterList':      GetTwitterHarvesterList,
    'GetTwitterUserList':           GetTwitterUserList,
    'GetTwitterSearchList':         GetTwitterSearchList,
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

def error(errorType, errorValue): return jsonResponse({'error': {'type':errorType, 'value':errorValue}})

def api_one_zero(request, command):
    if command == 'authent': return authent(request)
    elif 'oauth' in request.GET and request.GET['oauth'] == DEFAULT_OAUTH_KEY:
        return command_management(command, request.GET)
    else:
        return error('UnauthentifiedError', 'You must use a authentification token to communicate with me')



def command_management(command, GET):
    if command in AVAILABLE_COMMANDS:
        return AVAILABLE_COMMANDS[command](GET)
    else:
        return error('InvalidRequestError', 'Invalid request')




















