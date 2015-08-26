# coding=UTF-8


from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django import template
from django.template.defaultfilters import stringfilter
from django.db.models import Q

from fandjango.decorators import facebook_authorization_required
from fandjango.models import User as FanUser

import gviz_api
import datetime as dt
from django.http import HttpResponse
from itertools import izip_longest

from django.utils import simplejson

from snh.models.twittermodel import *
from snh.models.facebookmodel import *
from snh.models.youtubemodel import *
from snh.models.dailymotionmodel import *

from snh.utils import get_datatables_records, generate_csv_response

from settings import FACEBOOK_APPLICATION_ID, dLogger

import snhlogger
logger = snhlogger.init_logger(__name__, "view.log")


#
# FACEBOOK TOKEN
#
@login_required(login_url=u'/login/')
def request_fb_token(request):
    return  render_to_response(u'snh/test_token.html',{u'user': userfb})

@login_required(login_url=u'/login/')
def test_fb_token(request):
    token = FacebookSessionKey.objects.all()
    if not token:
        token = FacebookSessionKey.objects.create()
    else: token = token[0]
    print token.get_access_token()
    return  render_to_response(u'snh/test_token.html',
        {   'appId': FACEBOOK_APPLICATION_ID,
            'currentToken': token.get_access_token()})

@csrf_exempt
@login_required(login_url=u'/login/')
def fb_update_client_token(request):
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

fb_posts_fields = [

    ['fid','message','message_tags_raw','picture','link','name','caption','description',
    'source','properties_raw','icon','ftype','likes_from','likes_count','comments_count',
    'shares_count','place_raw','story','story_tags_raw','object_id','application_raw',],

    ['user__name','user__username','user__website','user__link','user__first_name','user__last_name',
    'user__gender','user__locale','user__languages_raw','user__third_party_id','user__installed_raw',
    'user__timezone_raw','user__updated_time','user__verified','user__bio','user__birthday',
    'user__education_raw','user__email','user__hometown','user__interested_in_raw',
    'user__location_raw','user__political','user__favorite_athletes_raw','user__favorite_teams_raw',
    'user__quotes','user__relationship_status','user__religion','user__significant_other_raw',
    'user__video_upload_limits_raw','user__work_raw','user__category','user__likes',
    'user__about','user__phone','user__checkins','user__picture','user__talking_about_count',],

    ['ffrom__name','ffrom__username','ffrom__website','ffrom__link','ffrom__first_name',
    'ffrom__last_name','ffrom__gender','ffrom__locale','ffrom__languages_raw','ffrom__third_party_id',
    'ffrom__installed_raw','ffrom__timezone_raw','ffrom__updated_time','ffrom__verified','ffrom__bio',
    'ffrom__birthday','ffrom__education_raw','ffrom__email','ffrom__hometown','ffrom__interested_in_raw',
    'ffrom__location_raw','ffrom__political','ffrom__favorite_athletes_raw','ffrom__favorite_teams_raw',
    'ffrom__quotes','ffrom__relationship_status','ffrom__religion','ffrom__significant_other_raw',
    'ffrom__video_upload_limits_raw','ffrom__work_raw','ffrom__category','ffrom__likes','ffrom__about',
    'ffrom__phone','ffrom__checkins','ffrom__picture','ffrom__talking_about_count',],
    ]

fb_comments_fields = [
    ['fid','message','created_time','likes','ftype',],

    ['post__fid','post__message','post__message_tags_raw','post__picture','post__link',
    'post__name','post__caption','post__description','post__source','post__properties_raw',
    'post__icon','post__ftype','post__likes_from','post__likes_count','post__comments_count',
    'post__shares_count','post__place_raw','post__story','post__story_tags_raw',
    'post__object_id','post__application_raw',],

    ['ffrom__name','ffrom__username','ffrom__website','ffrom__link','ffrom__first_name',
    'ffrom__last_name','ffrom__gender','ffrom__locale','ffrom__languages_raw','ffrom__third_party_id',
    'ffrom__installed_raw','ffrom__timezone_raw','ffrom__updated_time','ffrom__verified','ffrom__bio',
    'ffrom__birthday','ffrom__education_raw','ffrom__email','ffrom__hometown',],

    ['ffrom__interested_in_raw',
    'ffrom__location_raw','ffrom__political','ffrom__favorite_athletes_raw','ffrom__favorite_teams_raw',
    'ffrom__quotes','ffrom__relationship_status','ffrom__religion','ffrom__significant_other_raw',
    'ffrom__video_upload_limits_raw','ffrom__work_raw','ffrom__category','ffrom__likes','ffrom__about',
    'ffrom__phone','ffrom__checkins','ffrom__picture','ffrom__talking_about_count',],
    ]

@login_required(login_url=u'/login/')
def fb(request, harvester_id):
    facebook_harvesters = FacebookHarvester.objects.all()

    return  render_to_response(u'snh/facebook.html',{
                                                    u'fb_selected':True,
                                                    u'all_harvesters':facebook_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    'status_fields': izip_longest(*fb_posts_fields),
                                                    'comment_fields': izip_longest(*fb_comments_fields),
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
                                                    'status_fields': izip_longest(*fb_posts_fields),
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
                                                    'status_fields': izip_longest(*fb_posts_fields),
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

@login_required(login_url=u'/login/')
def dwld_fb_posts_csv(request):
    if debugging: dLogger.log('dwld_tw_status_csv')

    fields = request.GET.getlist('fields')
    columns = [field for field in fields if not field.startswith('user__') and not field.startswith('ffrom__')]
    columns += [field for field in fields if field.startswith('user__')]
    columns += [field for field in fields if field.startswith('ffrom__')]

    sColumns = ''
    for column in columns:
        sColumns += str(column)+','
    dLogger.log('sColumns: %s'%sColumns)
    aadata = []

    if 'harvester_id' in request.GET:
        harvester = get_object_or_404(FacebookHarvester, pmk_id=request.GET['harvester_id'])
        # merge two conditional filter in queryset:
        conditions = [Q(user=user) for user in harvester.fbusers_to_harvest.all()]
        statuses = FBPost.objects.filter(reduce(lambda x, y: x | y, conditions)).distinct()

    elif 'FBUser_id' in request.GET:
        user = get_object_or_404(FBUser, pmk_id=request.GET['FBUser_id'])
        statuses = user.postedStatuses.all()

    for status in statuses:
        adata = []
        user = status.user
        ffrom = status.ffrom
        for column in columns:
            if 'user__' in column:
                value = getattr(user, re.sub('user__', '', column))
            elif 'ffrom__' in column:
                value = getattr(ffrom, re.sub('ffrom__', '', column))
            elif column in ['likes_from',]:
                manager = getattr(status, column)
                value = manager.all()
            else:
                value = getattr(status, column)
            adata.append(unicode(value))
        aadata.append(adata)

    data = {'sColumns': sColumns, 'aaData': aadata}
    return generate_csv_response(data)

@login_required(login_url=u'/login/')
def dwld_fb_comments_csv(request):
    if debugging: dLogger.log('dwld_fb_comments_csv')

    fields = request.GET.getlist('fields')
    columns = [field for field in fields if not field.startswith('post__') and not field.startswith('ffrom__')]
    columns += [field for field in fields if field.startswith('post__')]
    columns += [field for field in fields if field.startswith('ffrom__')]

    sColumns = ''
    for column in columns:
        sColumns += str(column)+','
    dLogger.log('sColumns: %s'%sColumns)
    aadata = []

    if 'harvester_id' in request.GET:
        harvester_id = request.GET['harvester_id']
        harvester = get_object_or_404(FacebookHarvester, pmk_id=harvester_id)
        # merge two conditional filter in queryset:
        comments = FBComment.objects.filter(post__user__harvester_in_charge=harvester).distinct()

    for comment in comments:
        adata = []
        post = comment.post
        ffrom = comment.ffrom
        for column in columns:
            if column == 'post__likes_from':
                value = comment.post.likes_from.all()
            elif 'post__' in column:
                value = getattr(post, re.sub('post__', '', column))
            elif 'ffrom__' in column:
                value = getattr(ffrom, re.sub('ffrom__', '', column))
            else:
                value = getattr(comment, column)
            adata.append(unicode(value))
        aadata.append(adata)

    data = {'sColumns': sColumns, 'aaData': aadata}
    return generate_csv_response(data)

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
def get_fb_harvester_post_list(request, call_type, harvester_id):
    querySet = None
    #dLogger.log('harvester_id: %s'%harvester_id)
    
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
        if harvester_id == '0':
            querySet = FBPost.objects.all()
        else:
            harvester = get_list_or_404(FacebookHarvester, pk=harvester_id)[0]
            querySet = FBPost.objects.filter(user__harvester_in_charge=harvester)
    except:
        dLogger.exception("EXCEPTION OCCURED IN get_fb_harvester_post_list")
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
def get_fb_harvester_comment_list(request, call_type, harvester_id):
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
        if harvester_id == '0':
            querySet = FBComment.objects.all()
        else:
            harvester = get_list_or_404(FacebookHarvester, pk=harvester_id)[0]
            querySet = FBComment.objects.filter(post__user__harvester_in_charge=harvester).distinct()

    except ObjectDoesNotExist:
        pass
        dLogger.exception('ERROR OCCURED IN get_fb_harvester_comment_list:')
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


