import requests
import feedparser
import json
import csv
import io
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from xml.dom import minidom
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from .forms import CSVUploadForm, SearchForm, SearchDbForm
from .models import Server, Package, Content

class IndexViewServer(generic.ListView):
    template_name = 'list_server.html'
    context_object_name = 'server_list'
    def get_queryset(self):
        return Server.objects.order_by('name')

class IndexViewContent(generic.ListView):
    template_name = 'list_content.html'
#    template_name = 'qdetail.html'
    context_object_name = 'content_list'
    def get_queryset(self):
        sv_id = self.kwargs.get('sv_id')      
        return Content.objects.filter(sv_id_id=sv_id).select_related('pkg_name').select_related('sv_id').order_by('sv_pkg')
#        return Content.objects.filter(sv_id_id=sv_id).order_by('pkg_name_id').select_related('pkg_name').query
#        return Content.objects.filter(sv_id_id=sv_id).select_related('pkg_name_id').values()

class DbIndex(generic.ListView):
    template_name = 'list_db.html'
    context_object_name = 'db_list'
    def post(self, request, *args, **kwargs):
        request.session['item'] = self.request.POST.get('item', None)
        request.session['post'] = "on"
#        1/0
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tmp_post = ""
        tmp_item = ""
        if 'item' in self.request.session:
            initial_data = dict(item = self.request.session['item'])
        else:
            initial_data = dict(item = "")
        search_form = SearchDbForm(initial=initial_data)
        context['search_form'] = search_form
#        1/0
        return context

    def get_queryset(self):
        if 'item' in self.request.session:
            post = self.request.session['post']
            item = self.request.session['item']
#            1/0
            if len(item) > 0 and post == "on":
                self.request.session['post'] = "off"
                return Content.objects.select_related('pkg_name').select_related('sv_id').filter(pkg_name__pkg_name__contains = item).order_by('sv_id_id', 'pkg_name_id')
            else:
                return Content.objects.none()
        else:
            return Content.objects.none()

class DbImport(generic.FormView):
    template_name = 'import.html'
    context_object_name = 'content_list'
    success_url = reverse_lazy('vuln:db_import')
    form_class = CSVUploadForm

    def form_valid(self, form):
        form.save()
        return redirect('vuln:server_list')

def db_export(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="content.csv"'
    # HttpResponseオブジェクトはファイルっぽいオブジェクトなので、csv.writerにそのまま渡せます。
    writer = csv.writer(response)
    for content in Content.objects.all().select_related('pkg_name').select_related('sv_id').order_by('sv_id_id', 'pkg_name_id'):
        writer.writerow([content.sv_id.name, content.sv_id.ip, content.sv_id.os, content.sv_id.usage, content.sv_id.remark, content.pkg_name_id, content.version, content.pkg_name.architecture, content.pkg_name.description, content.pkg_name.remark])
    return response

def search_free(request):
    if request.method == "POST":
        form = SearchForm(request.POST)
        choices = (('1', 'All'), ('2', 'LOW'), ('3', 'MEDIUM'), ('4', 'HIGH'),('5', 'CRITICAL'))
        form.fields["severity"].choices = choices
        if form.is_valid():
            keyword = form.cleaned_data.get('keyword')
            start_date = (str(form.cleaned_data.get('start_year'))+
                        str(form.cleaned_data.get('start_month')).zfill(2)+
                        str(form.cleaned_data.get('start_day')).zfill(2))
            end_date = (str(form.cleaned_data.get('end_year'))+
                        str(form.cleaned_data.get('end_month')).zfill(2)+
                        str(form.cleaned_data.get('end_day')).zfill(2))
            target = form.cleaned_data.get('target')
            cpe1 = form.cleaned_data.get('cpe1')
            cpe2 = form.cleaned_data.get('cpe2')
            cpe3 = form.cleaned_data.get('cpe3')
            if cpe2:
                cpe = cpe1+":"+cpe2+":"+cpe3
            else:
                cpe =""
            severity = form.cleaned_data.get('severity')
            if target == "1":
                if cpe:
                    cpe = "cpe:/"+cpe
                keyword, errorcd, entries, count = api_myjvn(keyword, start_date, end_date, cpe, severity)
                return render(request, 'search_myjvn.html', {'key': keyword, 'err': errorcd, 'entries': entries, "count": count})
            else:
                cvss = form.cleaned_data.get('cvss')
                if cpe:
                    cpe = "cpe:2.3:"+cpe
                    cpe4 = form.cleaned_data.get('cpe4')
                    cpe5 = form.cleaned_data.get('cpe5')
                    cpe6 = form.cleaned_data.get('cpe6')
                    cpe7 = form.cleaned_data.get('cpe7')
                    if cpe4:
                        cpe = cpe+":"+cpe4
                        if cpe5:
                            cpe = cpe+":"+cpe5
                            if cpe6:
                                cpe = cpe+":"+cpe6
                                if cpe7:
                                    cpe = cpe+":"+cpe7 
                keyword, errorcd, entries, count = api_nvd(keyword, start_date, end_date, cpe, cvss, severity)
                return render(request, 'search_nvd.html', {'key': keyword, 'err': errorcd, 'entries': entries, "count": count})
    else:
        form = SearchForm()
        choice = []
        choice.append(("1", "ALL"))
        form.fields["severity"].choices = choice
    return render(request, 'search_free.html', {'form':form})

def search_nvd(request, sv_pkg):
    dbdata = Content.objects.get(sv_pkg=sv_pkg)
    today = datetime.today()
    lastmonth = today + relativedelta(months=-1)
    pkg = dbdata.pkg_name_id
    if pkg.find("-") != -1:
        chk_key = pkg[:pkg.find("-")].replace(" ","")
    else:
        chk_key = pkg.replace(" ","")
    if chk_key.find(":") != -1:
        chk_key = chk_key[:chk_key.find(":")]
    if chk_key.find(".") != -1:
        chk_key = chk_key[:chk_key.find(".")]
    keyword, errorcd, entries, count = api_nvd(chk_key, lastmonth.strftime('%Y%m%d'), today.strftime('%Y%m%d'), "", "", "1")
    return render(request, 'search_nvd.html', {'key': keyword, 'err': errorcd, 'entries': entries, "count": count})


def search_myjvn(request, sv_pkg):
    dbdata = Content.objects.get(sv_pkg=sv_pkg)
    today = datetime.today()
    lastyear = today + relativedelta(years=-1)
    pkg = dbdata.pkg_name_id
    if pkg.find("-") != -1:
        chk_key = pkg[:pkg.find("-")].replace(" ","")
    else:
        chk_key = pkg.replace(" ","")
    if chk_key.find(":") != -1:
        chk_key = chk_key[:chk_key.find(":")]
    if chk_key.find(".") != -1:
        chk_key = chk_key[:chk_key.find(".")]
    keyword, errorcd, entries, count = api_myjvn(chk_key, lastyear.strftime('%Y%m%d'), today.strftime('%Y%m%d'), "", "1")
    return render(request, 'search_myjvn.html', {'key': keyword, 'err': errorcd, 'entries': entries, "count": count})

def api_myjvn(key, start_date, end_date, cpe, severity):
    # error avoidance : ssl dh_key_too_small 
    try:
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
    except AttributeError:
        pass
    try:
        requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += 'HIGH:!DH:!aNULL'
    except AttributeError:
        pass

    total, resret, first = 50, 0, 1
    errcd = "none"
    entries = []
    keys = ["id", "title", "identifier", "version", "severity", "score"]
    severity_dict = {"2": "l", "3": "m", "4": "h", "5": "c"}
    while total >= (resret+first):
        if key:
            url = "https://jvndb.jvn.jp/myjvn?method=getVulnOverviewList&feed=hnd&keyword="+key
            search_key = key
        else:
            url = "https://jvndb.jvn.jp/myjvn?method=getVulnOverviewList&feed=hnd&cpeName="+cpe
            search_key = cpe
        if (severity is None) or (severity == "1"):
            pass
        else:
            url = url+"&severity="+severity_dict[severity]
            search_key = search_key + ":" + severity_dict[severity]
        search_key = search_key + ":" + start_date + "-" + end_date
        url = (url+
            "&startItem="+str(resret+first)+
            "&dateFirstPublishedStartY="+start_date[0:4]+
            "&dateFirstPublishedStartM="+start_date[4:6]+
            "&dateFirstPublishedStartD="+start_date[6:8]+
            "&dateFirstPublishedEndY="+end_date[0:4]+
            "&dateFirstPublishedEndM="+end_date[4:6]+
            "&dateFirstPublishedEndD="+end_date[6:8]+
            "&rangeDatePublic=n&rangeDatePublished=n")
        response = requests.get(url)

        dom = minidom.parseString(response.text)
        for item in dom.getElementsByTagName("item"):
            values = [item.getElementsByTagName("link")[0].childNodes[0].nodeValue,
                    item.getElementsByTagName("title")[0].childNodes[0].nodeValue]
            if len(item.getElementsByTagName("sec:identifier")):
                values.append(item.getElementsByTagName("sec:identifier")[0].childNodes[0].nodeValue)
            else:
                values.append(" ")
            if len(item.getElementsByTagName("sec:cvss")) == 0:
                values.extend([" ", " ", " "])
            else:
                for item_cvss in item.getElementsByTagName("sec:cvss"):
                    if len(item.getElementsByTagName("sec:cvss")) == 1:
                        values.extend([item_cvss.getAttribute("version"),
                                    item_cvss.getAttribute("score"),
                                    item_cvss.getAttribute("severity")])
                    else:
                        if item_cvss.getAttribute("version") == "3.0":
                            values.extend([item_cvss.getAttribute("version"),
                                        item_cvss.getAttribute("score"),
                                        item_cvss.getAttribute("severity")])
            if len(values) < 6:
                for i in range(6-len(values)):
                    values.append(" ")
            dic = dict(zip(keys, values))
            entries.append(dic)
        status = dom.getElementsByTagName("status:Status")
        if status[0].getAttribute("errCd"):
            errcd = status[0].getAttribute("errMsg")
        total = int(status[0].getAttribute("totalRes"))
        resret = int(status[0].getAttribute("totalResRet"))
        first = int(status[0].getAttribute("firstRes"))
        count = len(entries)    
        if count >= 500:
            break

        '''
        vulnerability = feedparser.parse(response.text)
        for entry in vulnerability.entries:
            values = [entry.id, entry.title]
            if "sec_identifier" in entry:
                values.append(entry.sec_identifier)
            else:
                values.append(" ")
            if "sec_cvss" in entry:
                values.extend([entry.sec_cvss["version"],
                               entry.sec_cvss["severity"],
                               entry.sec_cvss["score"]])
            else:
                values.extend([" ", " ", " "])
            dic = dict(zip(keys, values))
            entries.append(dic)
        status = vulnerability.feed.status_status 
        if status['errcd']:
            errcd = status['errmsg']
        total = int(status['totalres'])
        resret = int(status['totalresret'])
        first = int(status['firstres'])
        count = len(entries)    
        if count >= 500:
            break
        '''
#    print(1/0)
    return (search_key, errcd, entries, count)

def api_nvd(key, sdate, edate, cpe, cvss, severity):
    result, start, total = 0, 0, 2000
    errcd = "none"
    keys = ["cve_id", "description", "published", "lastModified", "version", "baseScore", "baseSeverity", "references"]
    entries = []
    while total > (result+start):
        if cpe:
            # Search by cpeName
            url = "https://services.nvd.nist.gov/rest/json/cves/2.0/?cpeName="+cpe+'&startIndex='+str(start)
            search_key = cpe
        elif key:
            # Search by keyword 
            url = "https://services.nvd.nist.gov/rest/json/cves/2.0/?keywordSearch="+key+'&startIndex='+str(start)
            search_key = key
        else:
            # Search by published datetime
            startdate = sdate[0:4]+"-"+sdate[4:6]+"-"+sdate[6:8]+"T00:00:00.000-09:00"
            enddate = edate[0:4]+"-"+edate[4:6]+"-"+edate[6:8]+"T23:59:59.999-09:00"
            start = start +result
            url = "https://services.nvd.nist.gov/rest/json/cves/2.0/?pubStartDate="+startdate+"&pubEndDate="+enddate+'&startIndex='+str(start)
            search_key = str(sdate) + "-" + str(edate)
        if cvss != "1":
            if (severity is None) or (severity == "1"):
                pass
            else:
                severity_dict = {"2": "LOW", "3": "MEDIUM", "4": "HIGH", "5": "CRITICAL"}
                url = url+"&cvssV"+cvss+"Severity="+severity_dict[severity]
                search_key = search_key + ":cvssV" + cvss + "-" + severity_dict[severity]
#        1/0
        response = requests.get(url)
        if response.status_code < 400:
            try:
                json_data = json.loads(response.text)
            except Exception as e:
                errcd = "requests_error: "+e
                result, start, total = 1, 0, 0
            else:
                result = json_data['resultsPerPage']
                total = json_data['totalResults']
                vulnerabilities = json_data['vulnerabilities']
                for vl in vulnerabilities:
                    values = ([
                        vl['cve']['id'],
                        vl['cve']['descriptions'][0]['value'],
                        vl['cve']['published'],
                        vl['cve']['lastModified']
                    ])
                    if 'cvssMetricV31' in vl['cve']['metrics']:
                        values.extend([
                            vl['cve']['metrics']['cvssMetricV31'][0]['cvssData']['version'],
                            vl['cve']['metrics']['cvssMetricV31'][0]['cvssData']['baseScore'],
                        ])
                        if 'baseSeverity' in vl['cve']['metrics']['cvssMetricV31'][0]['cvssData']:
                            values.append(vl['cve']['metrics']['cvssMetricV31'][0]['cvssData']['baseSeverity'])
                        else:
                            values.append(" ")
                    elif 'cvssMetricV30' in vl['cve']['metrics']:
                        values.extend([
                            vl['cve']['metrics']['cvssMetricV30'][0]['cvssData']['version'],
                            vl['cve']['metrics']['cvssMetricV30'][0]['cvssData']['baseScore'],
                        ])
                        if 'baseSeverity' in vl['cve']['metrics']['cvssMetricV30'][0]['cvssData']:
                            values.append(vl['cve']['metrics']['cvssMetricV30'][0]['cvssData']['baseSeverity'])
                        else:
                            values.append(" ")
                    elif 'cvssMetricV2' in vl['cve']['metrics']:
                        values.extend([
                            vl['cve']['metrics']['cvssMetricV2'][0]['cvssData']['version'],
                            vl['cve']['metrics']['cvssMetricV2'][0]['cvssData']['baseScore'],
                        ])
                        if 'baseSeverity' in vl['cve']['metrics']['cvssMetricV2'][0]['cvssData']:
                            values.append(vl['cve']['metrics']['cvssMetricV2'][0]['cvssData']['baseSeverity'])
                        else:
                            values.append(" ")
                    else:
                        values.extend([" ", " ", " "])
                    if 'references' in vl['cve']:
                        if len(vl['cve']['references']) > 0:
                            values.append(vl['cve']['references'][0]['url'])
                        else:
                            values.append(" ")
                    else:
                        values.append(" ")
                    dic = dict(zip(keys, values))
                    entries.insert(0, dic)
        else:
            errcd = "requests_error:"+str(response.status_code)
            result, start, total = 1, 0, 0
#    print(1/0)
    return(search_key, errcd, entries, total)