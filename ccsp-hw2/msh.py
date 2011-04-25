#!/usr/bin/env python
# -*- coding: utf8 -*-

###########################################################
# 04/23/2011 Yi Huang - CCSP_hw2
# Min-Sheng Healthcare
# - url: "http://www.e-ms.com.tw/"
###########################################################
from BeautifulSoup import BeautifulSoup
from django.utils import simplejson
from google.appengine.api import memcache, urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import re, urllib, pickle, logging

CACHE_EXPIRE = 86400
MSH_URL = 'http://netreg.e-ms.com.tw/netreg'

def get_url(page_name, data=None):
    global MSH_URL
    if data:
        page_name = '%s?%s' % (page_name, data)
    return '%s/%s' % (MSH_URL, page_name)

def urldecode(url):
    tmp = re.split('[?&]', url)
    return dict([tuple(t.split('=')) for t in tmp[1:]])

def dict2list(dic):
    ret = []
    for pair in dic.iteritems():
        ret.append({pair[0]: pair[1]})
    return ret;

def quote(s):
    return urllib.quote(s.encode('unicode-escape'))

def unquote(s):
    return s.decode('big5').encode('utf-8')

def parse_time(time):
    time = time.split('-')
    date = str(int(time[0])-1911) + ''.join(time[1:3])
    if len(time) > 3:
        apn = {'A':'1','B':'2','C':'3'}[time[3]]
        return date, apn
    return date

def pack_time(date, apn=None):
    date = '-'.join([str(int(date[0:3])+1911), date[3:5], date[5:7]])
    if not apn:
        return date
    return '%s-%s' % (date, {'1':'A','2':'B','3':'C'}[apn])

def query_all(page_name, parse=None):
    key = pickle.dumps(page_name)
    tmp = memcache.get(key)
    if tmp:
        return pickle.loads(tmp)
    url = urlfetch.fetch(get_url(page_name))
    soup = BeautifulSoup(url.content)
    dic, li = {}, soup.find('form').findAll('input')
    for ele in li:
        if ele.get('type') == 'radio':
            dic[ele.get('value')] = ele.nextSibling
    if parse:
        dic = parse(dic)
    global CACHE_EXPIRE
    memcache.set(key, pickle.dumps(dic), time=CACHE_EXPIRE)
    return dic

def query_single(page_name, id, parse=None):
    key = pickle.dumps((page_name, id))
    tmp = memcache.get(key)
    if tmp:
        return pickle.loads(tmp)
    data = urllib.urlencode({
        'DivDoctor': id,
        'submit': '%B0e%A5X'
    })
    url = urlfetch.fetch(get_url(page_name, data))
    soup = BeautifulSoup(url.content)
    dic, time, li = {}, [], soup.findAll('a')
    for ele in li:
        if ele.get('href').startswith('MakeSureReg.asp'):
            tmp = re.split('[()]', ele.next)
            dic[tmp[0]] = tmp[1]
            tmp = urldecode(ele.get('href'))
            time.append(pack_time(tmp['date'], tmp['apn']))
    if parse:
        dic = parse(dic)
    global CACHE_EXPIRE
    memcache.set(key, pickle.dumps((dic, time)), time=CACHE_EXPIRE)
    return dic, time

def query_clino(doctor, date):
    key = pickle.dumps((doctor, date))
    tmp = memcache.get(key)
    if tmp:
        return tmp
    data = urllib.urlencode({
        'DivDoctor': doctor,
        'submit': '%B0e%A5X'
    })
    url = urlfetch.fetch(get_url('QueryDClinByDoc.asp', data))
    clino, soup = None, BeautifulSoup(url.content)
    for ele in soup.findAll('a'):
        if ele.get('href').startswith('MakeSureReg.asp'):
            tmp = urldecode(ele.get('href'))
            if tmp['date'] == date:
                clino = tmp['clino']
                break
    global CACHE_EXPIRE
    memcache.set(key, clino, time=CACHE_EXPIRE)
    return clino

def check_fields(handler, fields):
    missing = {}
    for k in fields.keys():
        tmp = handler.request.get(k)
        if not tmp:
            missing.update({k: fields[k]})
        setattr(handler, k, tmp)
    return missing

def report_success(response, num):
    response.out.write(simplejson.dumps({
        'status': 0,
        'message': num
    }, ensure_ascii=False))

def report_error(response, message):
    response.out.write(simplejson.dumps({
        'status': 1,
        'message': message
    }, ensure_ascii=False))

def report_missing(response, missing):
    response.out.write(simplejson.dumps({
        'status': 2,
        'message': dict2list(missing)
    }, ensure_ascii=False))

class MshHandler(webapp.RequestHandler):
    def get(self):
        self.handle_request()
    def post(self):
        self.handle_request()

class DeptHandler(MshHandler):
    def handle_request(self):
        id = self.request.get('id')
        if not id:
            ret = dict2list(self.get_info())
        else:
            doctor, time = self.get_info(id)
            name = self.get_info()[id]
            ret = [
                {'id': id},
                {'name': name},
                {'doctor': dict2list(doctor)},
                {'time': time}
            ]
        self.response.out.write(
            simplejson.dumps(ret, ensure_ascii=False)
        )
    
    @classmethod
    def get_info(self, id=None):
        if id is None:
            return query_all('FromDivReg.asp')
        else:
            return query_single('QueryDClinByDiv.asp', id)

class DoctorHandler(MshHandler):
    def handle_request(self):
        id = self.request.get('id')
        if not id:
            ret = dict2list(self.get_info())
        else:
            dept, time = self.get_info(id)
            name = self.get_info()[id]
            ret = [
                {'id': id},
                {'name': name},
                {'dept': dict2list(dept)},
                {'time': time}
            ]
        self.response.out.write(
            simplejson.dumps(ret, ensure_ascii=False)
        )
    
    @classmethod
    def get_info(self, id=None):
        if id is None:
            return query_all('FromDoctorReg.asp', DoctorHandler._parse_all_)
        else:
            return query_single('QueryDClinByDoc.asp', id)
    
    @staticmethod
    def _parse_all_(dic):
        for key in dic:
            dic[key] = re.sub('M[0-9]+', '', dic[key])
        return dic

class RegisterHandler(MshHandler):
    def handle_request(self):
        fields = {
            'doctor': '醫生',
            'time': '看診時間',
            'id': '身分證字號',
            'birthday': '生日'
        }
        missing = check_fields(self, fields)
        if len(missing) > 0:
            return report_missing(self.response, missing)
        self.birthday = parse_time(self.birthday)
        url = self._check_status_(self._do_register_())
        if url is None:
            return
        final_url = url.final_url
        if final_url.startswith('ShowRegResult.asp'):
            num = self._parse_result_(url)
            return report_success(self.response, num)
        message = unquote(urldecode(final_url)['message'])
        return report_error(self.response, message)
    
    def _do_register_(self):
        self.date, self.apn = parse_time(self.time)
        self.clino = query_clino(self.doctor, self.date)
        data = urllib.urlencode({
            'idchart': 'id',
            'idchartno': self.id,
            'birthdate': self.birthday,
            'fvrvflag': 2,
            'clinic_date': self.date,
            'clinic_apn': self.apn,
            'clinic_no': self.clino,
            'Submit': '++%B0e%A5X++'
        })
        return urlfetch.fetch(get_url('CheckIdentity.asp', data))
    
    def _check_status_(self, url):
        final_url = url.final_url
        if final_url.startswith('MakeReg.asp'):
            return urlfetch.fetch(get_url(final_url))
        elif final_url.startswith('ConfirmReg.asp'):
            fields = {
                'name': '姓名',
                'area_code': '郵遞區號',
                'addr': '地址',
                'tel': '電話'
            }
            missing = check_fields(self, fields)
            if len(missing) > 0:
                return report_missing(self.response, missing)
            return self._continue_register_()
        return url
    
    def _continue_register_(self):
        data = urllib.urlencode({
            'pt_name': quote(self.name),
            'tel_no': self.tel,
            'area_code': self.area_code,
            'address': quote(self.addr),
            'idchart': 'id',
            'idchartno': self.id,
            'birth_date': self.birthday,
            'fvrvflag': 1,
            'clinic_date': self.date,
            'clinic_apn': self.apn,
            'clinic_no': self.clino,
            'Submit': '++%AA%EC%B6e%B1%BE%B8%B9++'
        })
        return urlfetch.fetch(get_url('MakeReg.asp', data))
    
    def _parse_result_(self, url):
        result = urldecode(url.final_url)['result']
        num = result.split('||')[7]
        return num
    
class CancelRegisterHandler(MshHandler):
    def handle_request(self):
        fields = {
            'num': '看診編號',
            'time': '看診時間',
            'id': '身分證字號',
            'birthday': '生日'
        }
        missing = check_fields(self, fields)
        if len(missing) > 0:
            return report_missing(self.response, missing)
        url = self._do_cancel_()
    
    def _do_cancel(self):
        self.date, self.apn = parse_time(self.time)
        data = urllib.urlencode({
            'CancelData': 'id,%s,%s,%s,%s,%s' % (
                self.id, self.date, self.apn, self.num, self.birthday
            ),
            'Submit': '++%B0h%B1%BE++'
        })
        return urlfetch.fetch(get_url('CancelReg.asp', data))

def main():
    application = webapp.WSGIApplication([
        ('/msh/dept', DeptHandler),
        ('/msh/doctor', DoctorHandler),
        ('/msh/register', RegisterHandler),
        ('/msh/cancel_register', CancelRegisterHandler),
    ], debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()