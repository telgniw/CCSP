#!/usr/bin/env python
# -*- coding: utf8 -*-

"""
    04/25/2011 Yi Huang - CCSP_hw2
    Min-Sheng Healthcare
    - url: "http://www.e-ms.com.tw/"
"""
from BeautifulSoup import BeautifulSoup
from django.utils import simplejson
from google.appengine.api import memcache, urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime import DeadlineExceededError
import re, urllib, pickle, logging

CACHE_EXPIRE = 86400
MSH_URL = 'http://netreg.e-ms.com.tw/netreg'

def get_url(page_name, data=None):
    """ get Min-Sheng Hospotal online register url """
    global MSH_URL
    if data:
        page_name = '%s?%s' % (page_name, data)
    return '%s/%s' % (MSH_URL, page_name)

def urldecode(url):
    """ parse url parameters to dict """
    tmp = re.split('[?&]', url)
    return dict([tuple(t.split('=')) for t in tmp[1:]])

def dict2list(dic):
    """ convert dict to list """
    ret = []
    for pair in dic.iteritems():
        ret.append({pair[0]: pair[1]})
    return ret;

def quote(s):
    """ encode for url parameter passing """
    return urllib.quote(s.encode('unicode-escape'))

def unquote(s):
    """ decode return message from Min-Sheng Hospotal """
    return urllib.unquote(s).decode('big5')

def parse_time(time):
    """ parse time from client """
    time = time.split('-')
    date = str(int(time[0])-1911) + ''.join(time[1:3])
    if len(time) > 3:
        apn = {'A':'1','B':'2','C':'3'}[time[3]]
        return date, apn
    return date

def pack_time(date, apn=None):
    """ pack time for client """
    date = '-'.join([str(int(date[0:3])+1911), date[3:5], date[5:7]])
    if not apn:
        return date
    return '%s-%s' % (date, {'1':'A','2':'B','3':'C'}[apn])

def query_all(page_name, parse=None):
    """ query full list of departments or doctors """
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
    """ query information for a department or a doctor """
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
        if 'MakeSureReg.asp' in ele.get('href'):
            tmp = re.split('[()]', ele.next)
            dic[tmp[0]] = tmp[1]
            tmp = urldecode(ele.get('href'))
            time.append(pack_time(tmp['date'], tmp['apn']))
    if parse:
        dic = parse(dic)
    global CACHE_EXPIRE
    memcache.set(key, pickle.dumps((dic, time)), time=CACHE_EXPIRE)
    return dic, time

def query_clino(doctor, date, apn):
    """ get clinic number by doctor and time """
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
        if 'MakeSureReg.asp' in ele.get('href'):
            tmp = urldecode(ele.get('href'))
            if tmp['date'] == date and tmp['apn'] == apn:
                clino = tmp['clino']
                break
    global CACHE_EXPIRE
    memcache.set(key, clino, time=CACHE_EXPIRE)
    return clino

def check_fields(handler, fields):
    """ check if request has missing fields """
    missing = {}
    for k in fields.keys():
        tmp = handler.request.get(k)
        if not tmp:
            missing.update({k: fields[k]})
        setattr(handler, k, tmp)
    return missing

def report_success(response, num):
    """ write success response message to client """
    response.out.write(simplejson.dumps({
        'status': 0,
        'message': num
    }, ensure_ascii=False))

def report_error(response, message):
    """ write error response message to client """
    response.out.write(simplejson.dumps({
        'status': 1,
        'message': message
    }, ensure_ascii=False))

def report_missing(response, missing):
    """ write missing fields response message to client """
    response.out.write(simplejson.dumps({
        'status': 2,
        'message': dict2list(missing)
    }, ensure_ascii=False))

class MshHandler(webapp.RequestHandler):
    """ basic handler for Min-Sheng Hospotal, use the same
        method handle_request() for both get() and put() """
    def get(self):
        self.handle_request()
    def post(self):
        self.handle_request()
    def handle_request(self):
        try:
            self._handle_request_()
        except DeadlineExceededError:
            report_error(self.response, 'Timeout')
        except (AttributeError, KeyError, ValueError):
            report_error(self.response, 'Error')

class DeptHandler(MshHandler):
    """ handling query for departments """
    def _handle_request_(self):
        id = self.request.get('id')
        if not id:
            ret = dict2list(self.get_info())
        else:
            name = self.get_info()[id]
            doctor, time = self.get_info(id)
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
    """ handling query for doctors """
    def _handle_request_(self):
        id = self.request.get('id')
        if not id:
            ret = dict2list(self.get_info())
        else:
            name = self.get_info()[id]
            dept, time = self.get_info(id)
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
        """ removing doctor id from doctor name list """
        for key in dic:
            dic[key] = re.sub('M[0-9]+', '', dic[key])
        return dic

class RegisterHandler(MshHandler):
    """ handling register """
    def _handle_request_(self):
        fields = {
            'doctor': u'醫生',
            'time': u'看診時間',
            'id': u'身分證字號',
            'birthday': u'生日'
        }
        missing = check_fields(self, fields)
        if len(missing) > 0:
            return report_missing(self.response, missing)
        url = self._check_status_(self._do_register_())
        if url is None:
            return
        final_url = url.final_url
        if 'ShowRegResult.asp' in final_url:
            ret = self._parse_result_(url)
            if ret:
                return report_success(self.response, ret)
        message = unquote(urldecode(final_url)['message'])
        return report_error(self.response, message)
    
    def _do_register_(self):
        """ 掛號 """
        self.date, self.apn = parse_time(self.time)
        self.clino = query_clino(self.doctor, self.date, self.apn)
        self.birthday = parse_time(self.birthday)
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
        """ 檢查掛號是否完成 """
        final_url = url.final_url
        if 'MakeReg.asp' in final_url:
            return urlfetch.fetch(get_url(final_url))
        elif 'ConfirmReg.asp' in final_url:
            fields = {
                'name': u'姓名',
                'area_code': u'郵遞區號',
                'addr': u'地址',
                'tel': u'電話'
            }
            missing = check_fields(self, fields)
            if len(missing) > 0:
                return report_missing(self.response, missing)
            return self._continue_register_()
        return url
    
    def _continue_register_(self):
        """ 初診資料 """
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
        """ 回傳看診編號 """
        result = unquote(urldecode(url.final_url)['result'])
        try:
            return result.split('||')[7]
        except IndexError:
            return None
    
class CancelRegisterHandler(MshHandler):
    """ handling cancel """
    def _handle_request_(self):
        fields = {
            'doctor': u'醫生',
            'time': u'看診時間',
            'id': u'身分證字號',
            'birthday': u'生日',
            'num': u'看診編號'
        }
        missing = check_fields(self, fields)
        if len(missing) > 0:
            return report_missing(self.response, missing)
        url = self._do_cancel_()
        message = unquote(urldecode(url.final_url)['message'])
        if u'成功' in message:
            return report_success(self.response, message)
        message = re.sub('\(CancelRegByIdNo\)\r\n', '', message)
        return report_error(self.response, message)
    
    def _do_cancel_(self):
        """ 取消掛號 """
        self.date, self.apn = parse_time(self.time)
        self.clino = query_clino(self.doctor, self.date, self.apn)
        self.birthday = parse_time(self.birthday)
        data = urllib.urlencode({
            'CancelData': 'id,%s,%s,%s,%s,%03d,%s' % (
                self.id, self.date, self.apn, self.clino, int(self.num), self.birthday
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
    ], debug=False)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()