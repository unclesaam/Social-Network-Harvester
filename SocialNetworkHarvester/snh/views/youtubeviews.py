# coding=UTF-8

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django import template
from django.template.defaultfilters import stringfilter

from fandjango.decorators import facebook_authorization_required
from fandjango.models import User as FanUser

import gviz_api
import datetime as dt
from django.http import HttpResponse

from snh.models.twittermodel import *
from snh.models.facebookmodel import *
from snh.models.youtubemodel import *
from snh.models.dailymotionmodel import *

from snh.utils import get_datatables_records

from settings import PROJECT_PATH

import snhlogger
logger = snhlogger.init_logger(__name__, "view.log")

#
# YOUTUBE
#
@login_required(login_url=u'/login/')
def yt(request, harvester_id):
    youtube_harvesters = YoutubeHarvester.objects.all()
    return  render_to_response(u'snh/youtube.html',{
                                                    u'yt_selected':True,
                                                    u'all_harvesters':youtube_harvesters,
                                                    u'harvester_id':harvester_id,
                                                  })

@login_required(login_url=u'/login/')
def yt_user_detail(request, harvester_id, userfid):
    youtube_harvesters = YoutubeHarvester.objects.all()
    user = get_list_or_404(YTUser, fid=userfid)[0]
    return  render_to_response(u'snh/youtube_detail.html',{
                                                    u'yt_selected':True,
                                                    u'all_harvesters':youtube_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'user':user,
                                                  })

@login_required(login_url=u'/login/')
def yt_video_detail(request, harvester_id, videoid):
    youtube_harvesters = YoutubeHarvester.objects.all()
    video = get_object_or_404(YTVideo, fid=videoid)
    video_url = ""
    if video.video_file_path:
        path_split = video.video_file_path.split(PROJECT_PATH)
        if len(path_split) > 1:
            video_url = path_split[1]

    return  render_to_response(u'snh/youtube_video.html',{
                                                    u'yt_selected':True,
                                                    u'all_harvesters':youtube_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'user':video.user,
                                                    u'video':video,
                                                    u'video_url':video_url,
                                                  })

#
# Youtube AJAX
#
@login_required(login_url=u'/login/')
def get_yt_list(request, call_type, harvester_id):
    querySet = None

    if harvester_id == "0":
        querySet = YTUser.objects.all()
    else:
        harvester = YoutubeHarvester.objects.get(pmk_id__exact=harvester_id)
        querySet = harvester.ytusers_to_harvest.all()

    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'fid',
                            1 : u'username',
                            2 : u'first_name',
                            3 : u'last_name',
                            4 : u'relationship',
                            5 : u'description',
                            6 : u'age',
                            7 : u'gender',
                            8 : u'location',
                            9 : u'company',
                            10 : u'last_web_access',
                            11 : u'subscriber_count',
                            12 : u'video_count',
                            13 : u'view_count',
                            }
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_yt_video_list(request, call_type, userfid):
    querySet = None
    #columnIndexNameMap is required for correct sorting behavior

    columnIndexNameMap = {
                            0 : u'published',
                            1 : u'fid',
                            2 : u'title',
                            3 : u'description',
                            4 : u'category',
                            5 : u'duration',
                            6: u'view_count',
                            7: u'favorite_count',
                            }
    try:
        user = get_list_or_404(YTUser, fid=userfid)[0]
        querySet = YTVideo.objects.filter(user=user)
    except ObjectDoesNotExist:
        pass
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_yt_comment_list(request, call_type, userfid):
    querySet = None
    #columnIndexNameMap is required for correct sorting behavior

    columnIndexNameMap = {
                            0 : u'published',
                            1 : u'user__username',
                            2 : u'video__user__username',
                            3 : u'video__fid',
                            4 : u'message',
                            5 : u'like_count',
                            6 : u'user__fid',
                            7 : u'video__user__fid',
                            }
    try:
        user = get_list_or_404(YTUser, fid=userfid)[0]
        querySet = YTComment.objects.filter(user=user)
    except ObjectDoesNotExist:
        pass
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_yt_videocomment_list(request, call_type, videofid):
    querySet = None
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'published',
                            1 : u'user__username',
                            2 : u'video__user__username',
                            3 : u'video__fid',
                            4 : u'message',
                            5 : u'like_count',
                            6 : u'user__fid',
                            7 : u'video__user__fid',
                            }    
    try:
        video = get_list_or_404(YTVideo, fid=videofid)[0]
        querySet = YTComment.objects.filter(video=video)
    except ObjectDoesNotExist:
        pass
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_ytvideo_chart(request, harvester_id, userfid):

    user = get_list_or_404(YTUser, fid=userfid)[0]
    count = YTVideo.objects.filter(user=user).count()

    fromto = YTVideo.objects.filter(user=user).order_by(u"published")
    base = fromto[0].published if count != 0 else dt.datetime.now()
    to = fromto[count-1].published if count != 0 else dt.datetime.now()

    days = (to - base).days + 1
    dateList = [ base + dt.timedelta(days=x) for x in range(0,days) ]
    description = {"date_val": ("date", "Date"),
                   "post_count": ("number", "Post count"),
                  }
    data = []
    for date in dateList:
        c = YTVideo.objects.filter(user=user).filter(published__year=date.year,published__month=date.month,published__day=date.day).count()
        data.append({"date_val":date, "post_count":c})

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)
    logger.debug(data_table.ToJSon())

    response =  HttpResponse(data_table.ToJSon(), mimetype='application/javascript')
    return response

@login_required(login_url=u'/login/')
def get_ytcomment_chart(request, harvester_id, userfid):

    user = get_list_or_404(YTUser, fid=userfid)[0]
    count = YTComment.objects.filter(user=user).count()

    fromto = YTComment.objects.filter(user=user).order_by(u"published")
    base = fromto[0].published if count != 0 else dt.datetime.now()
    to = fromto[count-1].published if count != 0 else dt.datetime.now()

    days = (to - base).days + 1
    dateList = [ base + dt.timedelta(days=x) for x in range(0,days) ]
    description = {"date_val": ("date", "Date"),
                   "post_count": ("number", "Post count"),
                  }
    data = []
    for date in dateList:
        c = YTComment.objects.filter(user=user).filter(published__year=date.year,published__month=date.month,published__day=date.day).count()
        data.append({"date_val":date, "post_count":c})

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)
    logger.debug(data_table.ToJSon())

    response =  HttpResponse(data_table.ToJSon(), mimetype='application/javascript')
    return response

@login_required(login_url=u'/login/')
def get_ytvideocomment_chart(request, harvester_id, videofid):

    video = get_list_or_404(YTVideo, fid=videofid)[0]
    count = YTComment.objects.filter(video=video).count()

    fromto = YTComment.objects.filter(video=video).order_by(u"published")
    base = fromto[0].published if count != 0 else dt.datetime.now()
    to = fromto[count-1].published if count != 0 else dt.datetime.now()

    days = (to - base).days + 1
    dateList = [ base + dt.timedelta(days=x) for x in range(0,days) ]
    description = {"date_val": ("date", "Date"),
                   "post_count": ("number", "Post count"),
                  }
    data = []
    for date in dateList:
        c = YTComment.objects.filter(video=video).filter(published__year=date.year,published__month=date.month,published__day=date.day).count()
        data.append({"date_val":date, "post_count":c})

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)
    logger.debug(data_table.ToJSon())

    response =  HttpResponse(data_table.ToJSon(), mimetype='application/javascript')
    return response
