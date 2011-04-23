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

def dict2list(dic):
    ret = []
    for pair in dic.iteritems():
        ret.append({pair[0]: pair[1]})
    return ret;

class MshHandler(webapp.RequestHandler):
    url = 'http://netreg.e-ms.com.tw/netreg'
    
    def get(self):
        self.handle_request()
    
    def post(self):
        self.handle_request()
    
    @staticmethod
    def get_url(path):
        return '%s/%s' % (MshHandler.url, path)

class InfoQueryHandler(MshHandler):
    @classmethod
    def _all_(self, page_name):
        key = pickle.dumps(page_name)
        tmp = None #memcache.get(key)
        if tmp is not None:
            dic = pickle.loads(tmp)
        else:
            global CACHE_EXPIRE
            url = urlfetch.fetch(
                MshHandler.get_url(page_name)
            )
            soup = BeautifulSoup(url.content)
            dic, li = {}, soup.find('form').findAll('input')
            for ele in li:
                if ele.get('type') == 'radio':
                    dic[ele.get('value')] = ele.nextSibling
            dic = self._parse_all_(dic)
            memcache.set(key, pickle.dumps(dic), time=CACHE_EXPIRE)
        return dic
    
    @classmethod
    def _single_(self, page_name, id):
        key = pickle.dumps((page_name, id))
        tmp = None #memcache.get(key)
        if tmp is not None:
            dic = pickle.loads(tmp)
        else:
            data = urllib.urlencode({
                'DivDoctor': id,
                'submit': '%B0e%A5X'
            })
            url = urlfetch.fetch(
                MshHandler.get_url(page_name) + '?' + data
            )
            soup = BeautifulSoup(url.content)
            dic, li = {}, soup.findAll('a')
            for ele in li:
                if ele.get('href').startswith('MakeSureReg.asp'):
                    tmp = re.split('[()]', ele.next)
                    dic.update({tmp[0]: tmp[1]})
            dic = self._parse_single_(dic)
            memcache.set(key, pickle.dumps(dic), time=CACHE_EXPIRE)
        return dic
    
    @classmethod
    def _parse_all_(self, dic):
        return dic
    
    @classmethod
    def _parse_single_(self, dic):
        return dic

class DeptHandler(InfoQueryHandler):
    def handle_request(self):
        id = self.request.get('id')
        if id:
            dic = self.get_info(id)
        else:
            dic = self.get_info()
        self.response.out.write(
            simplejson.dumps(dict2list(dic), ensure_ascii=False)
        )
    
    @classmethod
    def get_info(self, id=None):
        if id is None:
            return self._all_('FromDivReg.asp')
        else:
            return self._single_('QueryDClinByDiv.asp', id)

class DoctorHandler(InfoQueryHandler):
    def handle_request(self):
        id = self.request.get('id')
        if id:
            dic = self.get_info(id)
        else:
            dic = self.get_info()
        self.response.out.write(
            simplejson.dumps(dict2list(dic), ensure_ascii=False)
        )
    
    @classmethod
    def get_info(self, id=None):
        if id is None:
            return self._all_('FromDoctorReg.asp')
        else:
            return self._single_('QueryDClinByDoc.asp', id)
    
    @classmethod
    def _parse_all_(self, dic):
        for key in dic:
            dic[key] = re.sub('M[0-9]+', '', dic[key])
        return dic
    
    @classmethod
    def _parse_single_(self, dic):
        depts = {v:k for (k,v) in DeptHandler.get_info().iteritems()}
        return {depts[v]:v for v in dic.values()}

class RegisterHandler(MshHandler):
    def handle_request(self):
        self.response.out.write(output)

class CancelRegisterHandler(MshHandler):
    def handle_request(self):
        self.response.out.write(output)

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
