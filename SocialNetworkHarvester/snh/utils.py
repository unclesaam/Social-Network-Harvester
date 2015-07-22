from django.db.models import Q
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils.cache import add_never_cache_headers
from django.utils import simplejson
import csv, codecs, cStringIO
from xml.etree import ElementTree
import re

import snhlogger
logger = snhlogger.init_logger(__name__, "view.log")

from settings import dLogger

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

def generate_csv_response(d):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=output.csv'

    uw = UnicodeWriter(response)
    cols = d["sColumns"].split(",")
    uw.writerow(cols)
    for line in d["aaData"]:
        uw.writerow(line)

    return response

def get_datatables_records(request, querySet, columnIndexNameMap, call_type='web', jsonTemplatePath = None, *args):
    
    #dLogger.log('get_datatables_records()')
    #dLogger.log('    request: %s'%request)
    #dLogger.log('    querySet: %s'%querySet)
    #dLogger.log('    columnIndexNameMap: %s'%columnIndexNameMap)
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
    colitems = [columnIndexNameMap[key] for key in keys]
    for key in keys:
        if "len#" in columnIndexNameMap[key]:
            columnIndexNameMap[key] = re.sub(r'.*#', '', columnIndexNameMap[key])
            lenList.append(columnIndexNameMap[key])
            columnIndexNameMap.pop(key)
        else:
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
    if call_type != "csv":
        querySet = querySet[startRecord:endRecord] #get the slice
    sEcho = int(request.GET.get('sEcho',0)) # required echo response
    
    if jsonTemplatePath:
        jstonString = render_to_string(jsonTemplatePath, locals()) #prepare the JSON with the response, consider using : from django.template.defaultfilters import escapejs
        response = HttpResponse(jstonString, mimetype="application/javascript")
    
    else:
        aaData = []
        a = querySet.values(*columnIndexNameMap.values())
        #print 'a: %s'%a
        for row in a:
            #print ' row: %s'%row
            rowkeys = row.keys()
            rowvalues = row.values()
            rowlist = []
            for col in range(0,len(colitems)):
                for idx, val in enumerate(rowkeys):
                    if val == colitems[col]:
                        rowlist.append(unicode(rowvalues[idx]))
            #print ' rowlist: %s'%rowlist
            aaData.append(rowlist)
        #print 'aaData: %s'%aaData
        response_dict = {}
        response_dict.update({'aaData':aaData})
        response_dict.update({'sEcho': sEcho, 'iTotalRecords': iTotalRecords, 'iTotalDisplayRecords':iTotalDisplayRecords, 'sColumns':sColumns})
        response =  HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')

    #prevent from caching datatables result
    add_never_cache_headers(response)
    
    if call_type == "csv":
        response = generate_csv_response(response_dict)

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