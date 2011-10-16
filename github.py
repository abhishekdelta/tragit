#!/usr/bin/env python
#TODO NEED TO FIND A WAY TO ACCESS GITHUB VIA API TOKEN WITHOUT PASSWORD
import os
import base64
from httplib import HTTPSConnection
from json import JSONDecoder, JSONEncoder
import ConfigParser

config = ConfigParser.ConfigParser()
config.read('tragit.conf')
GITHUBLOGIN = config.get('github','USERNAME')
GITHUBPASSWORD = config.get('github','PASSWORD')
#GITHUBLOGIN = os.popen('git config --global github.user').read().strip()
#GITHUBTOKEN = os.popen('git config --global github.token').read().strip()
GITHUBAPI = 'api.github.com'

class GithubRequest(object):
    def __init__(self):
        self._create_connection()
        self._create_auth_header()

        self._decoder = JSONDecoder()
        self._encoder = JSONEncoder()


    def _create_auth_header(self):
        userpass = '%s:%s' % (GITHUBLOGIN, GITHUBPASSWORD)
        authkey = base64.b64encode(userpass).replace('\n','')
        self._auth_header = {}
        self._auth_header['Authorization'] = 'Basic %s' % authkey

        
    def _create_connection(self):
        self._connection = HTTPSConnection(GITHUBAPI)
        self._connection.connect()

        
    def request(self, method, url, params = None):
        if params != None:
            jsondata = self._encoder.encode(params)
        else:
            jsondata = None
        
        self._connection.request(method,url,jsondata,self._auth_header)
        response = self._connection.getresponse()
        jsonresponse = response.read()
        textresponse = self._decoder.decode(jsonresponse)
        return textresponse
    

def get_milestones(project):
    x = GithubRequest()
    data = x.request('GET','/repos/%s/%s/milestones' % (GITHUBLOGIN,project))
    return [x['title'] for x in data]


def create_milestone(project, ms_title, ms_desc = None, ms_dueon = None, ms_state = None):
    x = GithubRequest()
    milestone = {}
    milestone['title'] = ms_title
    
    if ms_desc != None:
        milestone['description'] = ms_desc
    
    if ms_state != None:
        milestone['state'] = ms_state
    
    if ms_dueon != None:
        milestone['due_on'] = ms_dueon
        
    data = x.request('POST','/repos/%s/%s/milestones' % (GITHUBLOGIN,project), milestone)
    
    if data['title'] == ms_title:
        return True
    return False
