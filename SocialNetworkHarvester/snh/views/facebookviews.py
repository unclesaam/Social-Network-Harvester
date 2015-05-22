# coding=UTF-8


from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django import template
from django.template.defaultfilters import stringfilter


from fandjango.decorators import facebook_authorization_required
from fandjango.models import User as FanUser

import gviz_api
import datetime as dt
from django.http import HttpResponse

from django.utils import simplejson

from snh.models.twittermodel import *
from snh.models.facebookmodel import *
from snh.models.youtubemodel import *
from snh.models.dailymotionmodel import *

from snh.utils import get_datatables_records

from settings import FACEBOOK_APPLICATION_ID

import snhlogger
logger = snhlogger.init_logger(__name__, "view.log")


#########################################################
debugging = 1
if debugging: 
    print "DEBBUGING ENABLED IN %s"%__name__
    debugLogger = snhlogger.init_custom_logger('debug'+__name__, "debugLogger.log", '(%(filename)-17s) %(message)s')
#########################################################

#
# FACEBOOK TOKEN
#
@login_required(login_url=u'/login/')
def request_fb_token(request):
    #fanu = FanUser.objects.all()
    #userfb = None
    #userfb = fanu[0].graph.get(u"me")
    return  render_to_response(u'snh/test_token.html',{u'user': userfb})

@login_required(login_url=u'/login/')
def test_fb_token(request):
    #fanu = FanUser.objects.all()
    return  render_to_response(u'snh/test_token.html',{'appId': FACEBOOK_APPLICATION_ID})

@csrf_exempt
@login_required(login_url=u'/login/')
def fb_update_client_token(request):
    if debugging: debugLogger.info('fb_update_client_token()')
    token = request.POST['token']
    currentSessionKey = FacebookSessionKey.objects.all()
    if not currentSessionKey:
        currentSessionKey = FacebookSessionKey.objects.create()
    else:
        currentSessionKey = currentSessionKey[0]
    currentSessionKey.set_access_token(token)


#
# FACEBOOK
#
@login_required(login_url=u'/login/')
def fb(request, harvester_id):
    facebook_harvesters = FacebookHarvester.objects.all()

    return  render_to_response(u'snh/facebook.html',{
                                                    u'fb_selected':True,
                                                    u'all_harvesters':facebook_harvesters,
                                                    u'harvester_id':harvester_id,
                                                  })

@login_required(login_url=u'/login/')
def fb_user_detail(request, harvester_id, username):
    facebook_harvesters = FacebookHarvester.objects.all()
    user = get_list_or_404(FBUser, username=username)[0]
    return  render_to_response(u'snh/facebook_detail.html',{
                                                    u'fb_selected':True,
                                                    u'all_harvesters':facebook_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'user':user,
                                                  })
@login_required(login_url=u'/login/')
def fb_userfid_detail(request, harvester_id, userfid):
    facebook_harvesters = FacebookHarvester.objects.all()
    user = get_list_or_404(FBUser, fid=userfid)[0]
    return  render_to_response(u'snh/facebook_detail.html',{
                                                    u'fb_selected':True,
                                                    u'all_harvesters':facebook_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'user':user,
                                                    })

@login_required(login_url=u'/login/')
def fb_post_detail(request, harvester_id, post_id):
    facebook_harvesters = FacebookHarvester.objects.all()
    post = get_object_or_404(FBPost, fid=post_id)
    return  render_to_response(u'snh/facebook_post.html',{
                                                    u'fb_selected':True,
                                                    u'all_harvesters':facebook_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'user':post.user,
                                                    u'post':post,
                                                  })

#
# Facebook AJAX
#
@login_required(login_url=u'/login/')
def get_fb_list(request, call_type, harvester_id):
    querySet = None

    if harvester_id == "0":
        querySet = FBUser.objects.all()
    else:
        harvester = FacebookHarvester.objects.get(pmk_id__exact=harvester_id)
        querySet = harvester.fbusers_to_harvest.all()

    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'pmk_id',
                            1 : u'fid',
                            2 : u'name',
                            3 : u'username',
                            4 : u'category',
                            5 : u'likes',
                            6 : u'about',
                            7 : u'phone',
                            8 : u'checkins',
                            9 : u'talking_about_count',
                            }
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_fb_post_list(request, call_type, userfid):
    querySet = None
    
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'created_time',
                            1 : u'fid',
                            2 : u'ffrom__username',
                            3 : u'name',
                            4 : u'description',
                            5 : u'caption',
                            6 : u'message',
                            7 : u'link__original_url',
                            8 : u'ftype',
                            9 : u'likes_count',
                            10: u'shares_count',
                            11: u'comments_count',
                            12: u'application_raw',
                            13: u'updated_time',
                            14: u'story',
                            15: u'ffrom__name',
                            16: u'ffrom__fid',
                            }
    try:
        user = get_list_or_404(FBUser, fid=userfid)[0]
        querySet = FBPost.objects.filter(user=user)
    except ObjectDoesNotExist:
        pass
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_fb_otherpost_list(request, call_type, userfid):
    querySet = None
    
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'created_time',
                            1 : u'fid',
                            2 : u'user__username',
                            3 : u'name',
                            4 : u'description',
                            5 : u'caption',
                            6 : u'message',
                            7 : u'link__original_url',
                            8 : u'ftype',
                            9 : u'likes_count',
                            10: u'shares_count',
                            11: u'comments_count',
                            12: u'application_raw',
                            13: u'updated_time',
                            14: u'story',
                            15: u'user__name',
                            16: u'user__fid',
                            }
    try:
        user = get_list_or_404(FBUser, fid=userfid)[0]
        querySet = FBPost.objects.filter(ffrom=user).exclude(user=user).order_by(u"created_time")
    except ObjectDoesNotExist:
        pass
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_fb_comment_list(request, call_type, userfid):
    querySet = None
    
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'created_time',
                            1 : u'ffrom__username',
                            2 : u'post__ffrom__name',
                            3 : u'post__fid',
                            4 : u'message',
                            5 : u'likes',
                            6: u'user_likes',
                            7: u'ftype',
                            8: u'ffrom__name',
                            9: u'ffrom__fid',
                            10: u'post__ffrom__fid',
                            }
    try:
        user = get_list_or_404(FBUser, fid=userfid)[0]
        querySet = FBComment.objects.filter(ffrom=user)
    except ObjectDoesNotExist:
        pass
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_fb_postcomment_list(request, call_type, postfid):
    querySet = None
    
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'created_time',
                            1 : u'ffrom__username',
                            2 : u'message',
                            3 : u'likes',
                            4: u'user_likes',
                            5: u'ftype',
                            6: u'ffrom__name',
                            7: u'ffrom__fid',
                            8: u'post__fid',
                            }
    try:
        post = get_list_or_404(FBPost, fid=postfid)[0]
        querySet = FBComment.objects.filter(post=post)
    except ObjectDoesNotExist:
        pass
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_fb_likes_list(request, call_type, postfid):
    querySet = None
    #columnIndexNameMap is required for correct sorting behavior

    columnIndexNameMap = {
                            0 : u'fid',
                            1 : u'name',
                            }
    try:
        post = get_list_or_404(FBPost, fid=postfid)[0]
        querySet = post.likes_from.all()
    except ObjectDoesNotExist:
        pass
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_wall_chart(request, harvester_id, userfid):

    user = get_list_or_404(FBUser, fid=userfid)[0]
    count = FBPost.objects.filter(user=user).count()

    fromto = FBPost.objects.filter(user=user).order_by(u"created_time")
    base = fromto[0].created_time if count != 0 else dt.datetime.now()
    to = fromto[count-1].created_time if count != 0 else dt.datetime.now()

    days = (to - base).days + 1
    dateList = [ base + dt.timedelta(days=x) for x in range(0,days) ]
    description = {"date_val": ("date", "Date"),
                   "post_count": ("number", "Post count"),
                  }
    data = []
    for date in dateList:
        c = FBPost.objects.filter(user=user).filter(created_time__year=date.year,created_time__month=date.month,created_time__day=date.day).count()
        data.append({"date_val":date, "post_count":c})

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)
    logger.debug(data_table.ToJSon())

    response =  HttpResponse(data_table.ToJSon(), mimetype='application/javascript')
    return response

@login_required(login_url=u'/login/')
def get_otherwall_chart(request, harvester_id, userfid):

    user = get_list_or_404(FBUser, fid=userfid)[0]
    count = FBPost.objects.filter(ffrom=user).exclude(user=user).count()

    fromto = FBPost.objects.filter(ffrom=user).exclude(user=user).order_by(u"created_time")
    base = fromto[0].created_time if count != 0 else dt.datetime.now()
    to = fromto[count-1].created_time if count != 0 else dt.datetime.now()

    days = (to - base).days + 1
    dateList = [ base + dt.timedelta(days=x) for x in range(0,days) ]
    description = {"date_val": ("date", "Date"),
                   "post_count": ("number", "Post count"),
                  }
    data = []
    for date in dateList:
        c = FBPost.objects.filter(ffrom=user).exclude(user=user).filter(created_time__year=date.year,created_time__month=date.month,created_time__day=date.day).count()
        data.append({"date_val":date, "post_count":c})

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)
    logger.debug(data_table.ToJSon())

    response =  HttpResponse(data_table.ToJSon(), mimetype='application/javascript')
    return response

@login_required(login_url=u'/login/')
def get_comment_chart(request, harvester_id, userfid):

    user = get_list_or_404(FBUser, fid=userfid)[0]
    count = FBComment.objects.filter(ffrom=user).count()

    fromto = FBComment.objects.filter(ffrom=user).order_by(u"created_time")
    base = fromto[0].created_time if count != 0 else dt.datetime.now()
    to = fromto[count-1].created_time if count != 0 else dt.datetime.now()

    days = (to - base).days + 1
    dateList = [ base + dt.timedelta(days=x) for x in range(0,days) ]
    description = {"date_val": ("date", "Date"),
                   "post_count": ("number", "Post count"),
                  }
    data = []
    for date in dateList:
        c = FBComment.objects.filter(ffrom=user).filter(created_time__year=date.year,created_time__month=date.month,created_time__day=date.day).count()
        data.append({"date_val":date, "post_count":c})

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)
    logger.debug(data_table.ToJSon())

    response =  HttpResponse(data_table.ToJSon(), mimetype='application/javascript')
    return response

@login_required(login_url=u'/login/')
def get_commentpost_chart(request, harvester_id, postfid):

    post = get_list_or_404(FBPost, fid=postfid)[0]
    count = FBComment.objects.filter(post=post).count()

    fromto = FBComment.objects.filter(post=post).order_by(u"created_time")
    base = fromto[0].created_time if count != 0 else dt.datetime.now()
    to = fromto[count-1].created_time if count != 0 else dt.datetime.now()

    days = (to - base).days + 1
    dateList = [ base + dt.timedelta(days=x) for x in range(0,days) ]
    description = {"date_val": ("date", "Date"),
                   "post_count": ("number", "Post count"),
                  }
    data = []
    for date in dateList:
        c = FBComment.objects.filter(post=post).filter(created_time__year=date.year,created_time__month=date.month,created_time__day=date.day).count()
        data.append({"date_val":date, "post_count":c})

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)
    logger.debug(data_table.ToJSon())

    response =  HttpResponse(data_table.ToJSon(), mimetype='application/javascript')
    return response


