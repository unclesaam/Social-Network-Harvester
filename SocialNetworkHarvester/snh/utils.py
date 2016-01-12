from django.db.models import Q
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils.cache import add_never_cache_headers
from django.utils import simplejson
from django.core.servers.basehttp import FileWrapper
import csv, codecs, cStringIO
from xml.etree import ElementTree
import re
import json
import ast
from django.core import serializers
import copy

import snhlogger
logger = snhlogger.init_logger(__name__, "view.log")

from settings import dLogger, TEMPO_JSON_FILE_PATH

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

@dLogger.debug
def generate_csv_stream(request, dataLength, data, filename='output.csv'):
    dLogger.log("generate_csv_stream()")
    def data():
        for i in xrange(dataLength):
            csvfile = StringIO.StringIO()
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(data[i])
            yield csvfile.getvalue()

    response = HttpResponse(data(), mimetype="text/csv")
    response["Content-Disposition"] = "attachment; filename=%s"%filename
    return response

def generate_csv_response(d, filename='output.csv'):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s'%filename

    uw = UnicodeWriter(response, encoding='UTF-8')
    cols = d["sColumns"].split(",")
    uw.writerow(cols)
    for line in d["aaData"]:
        uw.writerow(line)

    return response

#@dLogger.debug
def get_datatables_records(request, querySet, columnIndexNameMap, call_type='web', jsonTemplatePath = None, *args):
    #dLogger.log('get_datatables_records()')
    #dLogger.log('    request: %s'%request)
    #dLogger.log('    querySet: %s'%querySet)
   # dLogger.log('    columnIndexNameMap: %s'%columnIndexNameMap)
    #dLogger.log('    call_type: %s'%call_type)
    #dLogger.log('    jsonTemplatePath: %s'%jsonTemplatePath)
    """
    Usage: 
        querySet: query set to draw data from.
        columnIndexNameMap: field names in order to be displayed.
        jsonTemplatePath: optional template file to generate custom json from.  If not provided it will generate the data directly from the model.

    """

    cols = int(request.GET.get('iColumns',0)) # Get the number of columns
    iDisplayLength =  min(int(request.GET.get('iDisplayLength',10)),100)     #Safety measure. If someone messes with iDisplayLength manually, we clip it to the max value of 100.
    startRecord = int(request.GET.get('iDisplayStart',0)) # Where the data starts from (page)
    endRecord = startRecord + iDisplayLength  # where the data ends (end of page)
    
    # Pass sColumns
    keys = columnIndexNameMap.keys()
    lenList = []
    keys.sort()
    #colitems = [columnIndexNameMap[key] for key in keys]
    colitems = []
    for key in keys:
        if "len#" in columnIndexNameMap[key]:
            #columnIndexNameMap[key] = re.sub(r'.*#', '', columnIndexNameMap[key])
            lenList.append(columnIndexNameMap[key])
            #columnIndexNameMap.pop(key)
        colitems.append(columnIndexNameMap[key])
    sColumns = ",".join(map(unicode,colitems))


    if querySet is None:
        response_dict = {}
        response_dict.update({'aaData':[]})
        response_dict.update({'sEcho': int(request.GET.get('sEcho',0)), 'iTotalRecords': 0, 'iTotalDisplayRecords':0, 'sColumns':sColumns})
        response =  HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
        #prevent from caching datatables result
        add_never_cache_headers(response)
        return response
    
    # Ordering data
    iSortingCols =  int(request.GET.get('iSortingCols',0))
    asortingCols = []
        
    if iSortingCols:
        for sortedColIndex in range(0, iSortingCols):
            sortedColID = int(request.GET.get('iSortCol_'+unicode(sortedColIndex),0))
            if request.GET.get('bSortable_{0}'.format(sortedColID), 'false')  == 'true':  # make sure the column is sortable first
                sortedColName = columnIndexNameMap[sortedColID]
                sortingDirection = request.GET.get('sSortDir_'+unicode(sortedColIndex), 'asc')
                if sortingDirection == 'desc':
                    sortedColName = '-'+sortedColName
                asortingCols.append(sortedColName) 
        querySet = querySet.order_by(*asortingCols)

    # Determine which columns are searchable
    searchableColumns = []
    for col in range(0,cols):
        #logger.debug(col)
        if request.GET.get('bSearchable_{0}'.format(col), False) == 'true': searchableColumns.append(columnIndexNameMap[col])

    # Apply filtering by value sent by user
    customSearch = request.GET.get('sSearch', '').encode('utf-8');
    if customSearch != '':
        outputQ = None
        first = True
        for searchableColumn in searchableColumns:
            kwargz = {searchableColumn+"__icontains" : customSearch}
            outputQ = outputQ | Q(**kwargz) if outputQ else Q(**kwargz)  
        querySet = querySet.filter(outputQ)

    # Individual column search 
    outputQ = None
    for col in range(0,cols):
        if request.GET.get('sSearch_{0}'.format(col), False) > '' and request.GET.get('bSearchable_{0}'.format(col), False) == 'true':
            kwargz = {columnIndexNameMap[col]+"__icontains" : request.GET['sSearch_{0}'.format(col)]}
            outputQ = outputQ & Q(**kwargz) if outputQ else Q(**kwargz)
    if outputQ: querySet = querySet.filter(outputQ)
        
    iTotalRecords = iTotalDisplayRecords = querySet.count() #count how many records match the final criteria
    total_query_set = querySet
    if call_type != "csv":
        querySet = querySet[startRecord:endRecord] #get the slice
    sEcho = int(request.GET.get('sEcho',0)) # required echo response
    
    # Construct the response table
    if jsonTemplatePath:
        jstonString = render_to_string(jsonTemplatePath, locals()) #prepare the JSON with the response, consider using : from django.template.defaultfilters import escapejs
        response = HttpResponse(jstonString, mimetype="application/javascript")
    
    else:
        aaData = []
        values = [value for value in columnIndexNameMap.values() if value not in lenList]
        a = querySet.values(*values)

        # retrieve the length of dataset-size related columns
        if len(lenList) > 0:
            for elem in a:
                for new_elem in lenList:
                    len_elem = re.sub(r'len#', '', new_elem)
                    kwarg = {elem.keys()[0]:elem[elem.keys()[0]]}
                    elem[new_elem] = getattr(total_query_set.get(**kwarg),len_elem).count()


        for row in a:
            rowkeys = row.keys()
            rowvalues = row.values()
            rowlist = []

            for col in range(0,len(colitems)):
                for idx, val in enumerate(rowkeys):
                    if val == colitems[col]:
                        rowlist.append(unicode(rowvalues[idx]))
            aaData.append(rowlist)
        response_dict = {}
        response_dict.update({'aaData':aaData})
        response_dict.update({'sEcho': sEcho, 'iTotalRecords': iTotalRecords, 'iTotalDisplayRecords':iTotalDisplayRecords, 'sColumns':sColumns})
        response =  HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')

    #prevent from caching datatables result
    add_never_cache_headers(response)
    
    if call_type == "csv":
        response = generate_csv_response(response_dict)

    return response

def twUserAjaxTableError(text):
    response = HttpResponse(json.dumps({"sColumns": "created_at,fid,text,retweet_count,retweeted,source", 
            "iTotalRecords": 1, 
            "aaData": [["test", "0", text, "0", "False", "test"]],
            "sEcho": 0, 
            "iTotalDisplayRecords": 1}), 
        mimetype='application/javascript')
    add_never_cache_headers(response)
    return response

def xml_formater(base):
    """
    Return a string formated as if it were an XML structure, Assuming 
    the base string has has the standard XML syntax
    """
    def indent(elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    root = ElementTree.fromstring(base)
    indent(root)
    return ElementTree.tostring(root, encoding="us-ascii", method="xml")

def Twitter_raw_json_posts_data(queryName,querySet):
    '''works with Twitter posts only
    '''
    #dLogger.log('raw_json_data()')

    open(TEMPO_JSON_FILE_PATH, 'w').close()
    temporary_file = open(TEMPO_JSON_FILE_PATH, 'w')
    for query in querySet:
        raw_set = query.raw_twitter_response.all()
        if len(raw_set) > 0:
            data = ast.literal_eval(raw_set[0].data)
        else:

            serialize = lambda query: json.loads(serializers.serialize('json', [query]))[0]['fields']

            serialized_post = serialize(query)
            serialized_post['hashtags'] = [hashtag.text for hashtag in query.hash_tags.all()]
            serialized_post['text_urls'] = [url.original_url for url in query.text_urls.all()]
            data = format_serialized_obj(serialized_post, 
                                    {'fid' : 'id',
                                    'error_on_update' : '#del',
                                    'hash_tags': '#del',
                                    'model_update_date': '#del'})
            serialized_user = serialize(query.user)
            formated_user = format_serialized_obj(serialized_user, 
                                    {'error_on_update': '#del',
                                    'error_triggered': '#del',
                                    'fid': 'id',
                                    'harvester': '#del',
                                    'last_harvested_status': '#del',
                                    'model_update_date': '#del',
                                    'last_valid_status_fid':'#del',
                                    })
            if query.user.profile_image_url:
                formated_user['profile_image_url'] = query.user.profile_image_url.original_url
            if query.user.profile_background_image_url:
                formated_user['profile_background_image_url'] = query.user.profile_background_image_url.original_url

            data['user'] = formated_user
        temporary_file.write(json.dumps(data)+'\n')
        dLogger.pretty(data)

    temporary_file.close()
    temporary_file = open(TEMPO_JSON_FILE_PATH, 'r')

    response = HttpResponse(FileWrapper(temporary_file), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename=%s.json'%queryName
    return response



def format_serialized_obj(obj, translations):
    obj = copy.deepcopy(obj)
    for key in translations:
        if key in obj:
            if translations[key] != '#del':
                obj[translations[key]] = obj[key]
            del obj[key]
    return obj
