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
import facebook

from django.utils import simplejson

from snh.models.twittermodel import *
from snh.models.facebookmodel import *
from snh.models.youtubemodel import *
from snh.models.dailymotionmodel import *

from snh.utils import get_datatables_records, generate_csv_response

from settings import FACEBOOK_APPLICATION_ID, dLogger
import re
import csv, codecs, cStringIO

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
    client = facebook.GraphAPI(access_token=token.get_access_token())
    extendedToken = client.extend_access_token(app_id=FACEBOOK_APPLICATION_ID, app_secret=FACEBOOK_APPLICATION_SECRET_KEY)
    sessionKey[0].set_access_token(extendedToken['access_token']) # Insure that the token will be valid for another two months
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
    return HttpResponse('Done.')


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
    'user__quotes',],

    ['user__relationship_status','user__religion','user__significant_other_raw',
    'user__video_upload_limits_raw','user__work_raw','user__category','user__likes',
    'user__about','user__phone','user__checkins','user__picture','user__talking_about_count',
    'ffrom__name','ffrom__username','ffrom__website','ffrom__link','ffrom__first_name',
    'ffrom__last_name','ffrom__gender','ffrom__locale','ffrom__languages_raw','ffrom__third_party_id',
    'ffrom__installed_raw','ffrom__timezone_raw','ffrom__updated_time',],

    ['ffrom__verified','ffrom__bio','ffrom__birthday','ffrom__education_raw','ffrom__email','ffrom__hometown','ffrom__interested_in_raw',
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

choiceYears = [i for i in range(2000,2021)]
choiceMonths = [i for i in range(1,13)]
choiceDays = [i for i in range(1,32)]
present = dt.datetime.now()
now = [present.year, present.month, present.day]

@login_required(login_url=u'/login/')
def fb(request, harvester_id):
    facebook_harvesters = FacebookHarvester.objects.all()

    return  render_to_response(u'snh/facebook.html',{
                                                    u'fb_selected':True,
                                                    u'all_harvesters':facebook_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    'status_fields': izip_longest(*fb_posts_fields),
                                                    'comment_fields': izip_longest(*fb_comments_fields),
                                                    'years':choiceYears,
                                                    'months':choiceMonths,
                                                    'days':choiceDays,
                                                    "now":now,
                                                  })

@login_required(login_url=u'/login/')
def fb_user_detail(request, harvester_id, username):
    facebook_harvesters = FacebookHarvester.objects.all()
    user = get_list_or_404(FBUser, username=username)[0]
    wall_chart = user.postedStatuses.count() > 1
    otherwall_chart = user.postsOnWall.exclude(user=user).count() > 1
    comment_chart = user.postedComments.count() > 1
    return  render_to_response(u'snh/facebook_detail.html',{
                                                    u'fb_selected':True,
                                                    u'all_harvesters':facebook_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'user':user,
                                                    'status_fields': izip_longest(*fb_posts_fields),
                                                    'years':choiceYears,
                                                    'months':choiceMonths,
                                                    'days':choiceDays,
                                                    "now":now,
                                                    'wall_chart':wall_chart,
                                                    'otherwall_chart':otherwall_chart,
                                                    'comment_chart':comment_chart,
                                                  })
@login_required(login_url=u'/login/')
def fb_userfid_detail(request, harvester_id, userfid):
    facebook_harvesters = FacebookHarvester.objects.all()
    user = get_list_or_404(FBUser, fid=userfid)[0]
    wall_chart = user.postedStatuses.count() > 1
    otherwall_chart = user.postsOnWall.exclude(user=user).count() > 1
    comment_chart = user.postedComments.count() > 1
    return  render_to_response(u'snh/facebook_detail.html',{
                                                    u'fb_selected':True,
                                                    u'all_harvesters':facebook_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'user':user,
                                                    'status_fields': izip_longest(*fb_posts_fields),
                                                    'years':choiceYears,
                                                    'months':choiceMonths,
                                                    'days':choiceDays,
                                                    'wall_chart':wall_chart,
                                                    'otherwall_chart':otherwall_chart,
                                                    'comment_chart':comment_chart,
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

    start, end = 0, None
    if 'range' in request.GET:
        rng = request.GET['range']
        start, end = re.split('-', rng)

    harvester_id, FBUser_id = None, None

    if 'harvester_id' in request.GET:
        harvester_id = request.GET['harvester_id']
        if harvester_id == '0':
            statuses = FBPost.objects.all()
            filename='all_FBPosts'
        else:
            harvester = get_object_or_404(FacebookHarvester, pmk_id=harvester_id)
            # merge two conditional filter in queryset:
            conditions = [Q(user=user) for user in harvester.fbusers_to_harvest.all()]
            statuses = FBPost.objects.filter(reduce(lambda x, y: x | y, conditions)).distinct()
            filename = '%s_FBPosts'%re.sub(' ', '_', unicode(harvester))


    elif 'FBUser_id' in request.GET:
        FBUser_id = request.GET['FBUser_id']
        user = get_object_or_404(FBUser, pmk_id=FBUser_id)
        statuses = user.postedStatuses.all()
        filename = '%s_FBPosts'%re.sub(' ', '_', unicode(user))

    startYear = request.GET['startYear']
    startMonth = request.GET['startMonth']
    startDay = request.GET['startDay']
    stopYear = request.GET['stopYear']
    stopMonth = request.GET['stopMonth']
    stopDay = request.GET['stopDay']

    try:
        startDate = datetime(year=int(startYear),
            month=int(startMonth),day=int(startDay))
        stopDate = datetime(year=int(stopYear),
            month=int(stopMonth),day=int(stopDay))
    except:
        return render_to_response('500.html', {'referer':request.META.get('HTTP_REFERER'),
            'message': 'Please enter a valid date'})

    statuses = statuses.filter(created_time__gte=startDate, created_time__lte=stopDate)[start:end]

    filename += '_%s-%s-%s_to_%s-%s-%s'%(
        startYear,startMonth,startDay,
        stopYear,stopMonth,stopDay
        )

    if end:
        filename += '_%s-%s'%(start,int(end)-1)


    count = statuses.count()
    '''
    step_size = 10000
    if count > step_size:
        files = []
        for i in range(0, count, step_size):
            url = '/dwld_fb_posts_csv?range=%s-%s'%(i,i+step_size)
            if FBUser_id:
                url += '&FBUser_id=%s'%FBUser_id
            elif harvester_id:
                url += '&harvester_id=%s'%harvester_id
            for field in fields:
                url += '&fields=%s'%field
            for (key,value) in {'startYear':startYear,'startMonth':startMonth,
                    'startDay':startDay,'stopYear':stopYear,
                    'stopMonth':stopMonth,'stopDay':stopDay}.iteritems():
                url += '&'+key+'='+value
            files.append( ('%s_%s-%s.csv'%(filename,i,i+step_size-1), url))
        context = {'files': files}
        return render_to_response('snh/multiple_files_download.html', context)
    
    path = "F:\Libraries\Documents\ASPIRA\Quebec 2012 fb data\Elections_Quebec_2012_FBPosts_2000-1-1_to_2015-12-5.csv"
    f = open("F:\Libraries\Documents\ASPIRA\Quebec 2012 fb data\Elections_Quebec_2012_FBPosts_2000-1-1_to_2015-12-5.csv",'wb')
    csvWriter = csv.writer(f, delimiter=',')

    #dLogger.log(columns)
    csvWriter.writerow(columns)

    num = 0
    print('')
    BAR_LENGTH = 20
    for status in statuses:
        num+=1
        adata = []
        user = status.user
        ffrom = status.ffrom
        for column in columns:
            if 'user__' in column:
                value = getattr(user, re.sub('user__', '', column))
            elif 'ffrom__' in column:
                if ffrom:
                    value = getattr(ffrom, re.sub('ffrom__', '', column))
                else:
                    value = 'None'
            elif column in ['likes_from',]:
                manager = getattr(status, column)
                value = manager.all()
            else:
                value = getattr(status, column)
            adata.append(unicode(value).encode('utf-8'))
        csvWriter.writerow(adata)
        if num % 100 == 0:
            print '\r',
            print 'Progress:[%s%s]%i%%'%('#'*(num*BAR_LENGTH//count),
                ' '*(BAR_LENGTH - num*BAR_LENGTH//count),int(num*100/count)),
    print('completed')



    '''
    response = HttpResponse(dataStream(columns, statuses), mimetype="text/csv")
    response["Content-Disposition"] = "attachment; filename=%s"%filename+'.csv'
    response['Content-Length'] = count*1500 #approximate size in bytes 
    return response

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

    start, end = 0,None
    if 'range' in request.GET:
        rng = request.GET['range']
        start, end = re.split('-', rng)

    if 'harvester_id' in request.GET:
        harvester_id = request.GET['harvester_id']
        if harvester_id == '0':
            comments = FBComment.objects.all()
            filename='all_FBComments'
        else:
            harvester = get_object_or_404(FacebookHarvester, pmk_id=harvester_id)
            # merge two conditional filter in queryset:
            comments = FBComment.objects.filter(post__user__harvester_in_charge=harvester).distinct()
            filename='%s_FBComments'%re.sub(' ', '_', unicode(harvester))

    startYear = request.GET['startYear']
    startMonth = request.GET['startMonth']
    startDay = request.GET['startDay']
    stopYear = request.GET['stopYear']
    stopMonth = request.GET['stopMonth']
    stopDay = request.GET['stopDay']

    try:
        startDate = datetime(year=int(startYear),
            month=int(startMonth),day=int(startDay))
        stopDate = datetime(year=int(stopYear),
            month=int(stopMonth),day=int(stopDay))
    except:
        return render_to_response('500.html', {'referer':request.META.get('HTTP_REFERER'),
            'message': 'Please enter a valid date'})

    comments = comments.filter(created_time__gte=startDate, created_time__lte=stopDate)[start:end]

    filename += '_%s-%s-%s_to_%s-%s-%s'%(
        startYear,startMonth,startDay,
        stopYear,stopMonth,stopDay
        )

    if end:
        filename += '_%s-%s'%(start,int(end)-1)         
    
    count = comments.count()
    '''
    step_size = 10000
    if count > step_size:
        files = []
        for i in range(0, count, step_size):
            url = '/dwld_fb_comments_csv?harvester_id=%s&range=%s-%s'%(harvester_id,i,i+step_size)
            for field in fields:
                url += '&fields=%s'%field
            for (key,value) in {'startYear':startYear,'startMonth':startMonth,
                    'startDay':startDay,'stopYear':stopYear,
                    'stopMonth':stopMonth,'stopDay':stopDay}.iteritems():
                url += '&'+key+'='+value
            files.append( ('%s_%s-%s.csv'%(filename,i,i+step_size-1), url))
        context = {'files': files}
        return render_to_response('snh/multiple_files_download.html', context)
    '''
    '''

    path = "F:\Libraries\Documents\ASPIRA\Quebec 2012 fb data\Elections_Quebec_2012_FBComments_2000-1-1_to_2015-12-05.csv"
    f = open(path,'wb')
    csvWriter = csv.writer(f, delimiter=',')

    #dLogger.log(columns)
    csvWriter.writerow(columns)
    num = 0
    print('')
    BAR_LENGTH = 20
    print 'Progress:[%s%s]%i%%'%('#'*(num*BAR_LENGTH//count),
            ' '*(BAR_LENGTH - num*BAR_LENGTH//count),int(num*100/count)),
    
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
                if ffrom:
                    value = getattr(ffrom, re.sub('ffrom__', '', column))
                else: 
                    value = 'None'
            else:
                value = getattr(comment, column)
            adata.append(unicode(value).encode('utf-8'))

        aadata.append(adata)
        csvWriter.writerow(adata)
        if num % 100 == 0:
            print '\r',
            print 'Progress:[%s%s]%i%%'%('#'*(num*BAR_LENGTH//count),
                ' '*(BAR_LENGTH - num*BAR_LENGTH//count),int(num*100/count)),
    return HttpResponse('done')
    '''

    response = HttpResponse(dataStream(columns, comments), mimetype="text/csv")
    response["Content-Disposition"] = "attachment; filename=%s"%filename+'.csv'
    response['Content-Length'] = count*1500 #approximate size in bytes 
    return response
    

@dLogger.debug
def getFormatedFbData(element, columns): # element can be a status or comment
    #if debugging: dLogger.log('    element: %s'%element)
    adata = []
    if hasattr(element, 'user'):
        user = element.user
    if hasattr(element, 'ffrom'):
        ffrom = element.ffrom
    if hasattr(element, 'post'):
        post = element.post
    for column in columns:
        if column == 'post__likes_from':
            value = post.likes_from.all()
        elif 'post__' in column:
                value = getattr(post, re.sub('post__', '', column))
        elif 'user__' in column:
            value = getattr(user, re.sub('user__', '', column))
        elif 'ffrom__' in column:
            if ffrom:
                value = getattr(ffrom, re.sub('ffrom__', '', column))
            else:
                value = 'None'
        elif column in ['likes_from',]:
            manager = getattr(element, column)
            value = manager.all()
        else:
            value = getattr(element, column)
        adata.append(unicode(value).encode('utf-8'))
    return adata

'''
    CSV streaming solution.
    Code found @ http://stackoverflow.com/questions/5146539/streaming-a-csv-file-in-django (thanks again Stackoverflow!)
'''
def dataStream(columns, statuses):

    csvfile = cStringIO.StringIO()
    csvwriter = csv.writer(csvfile)

    def read_and_flush():
        csvfile.seek(0)
        data = csvfile.read()
        csvfile.seek(0)
        csvfile.truncate()
        return data

    firstLine = True
    for i in range(statuses.count()):
        if firstLine:
            csvwriter.writerow(columns)
            firstLine = False
        else:
            csvwriter.writerow(getFormatedFbData(statuses[i], columns))
        data = read_and_flush()
        yield data

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


