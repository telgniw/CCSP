#!/usr/bin/env python

from google.appengine.api import users
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import util, template
import urllib2, logging

class Message(db.Model):
    author = db.UserProperty()
    content = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        messages = Message.all().order('timestamp')
        output = template.render("index.html", {
            'user': user,
            'messages': messages
        })
        self.response.out.write(output)

class SendHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        content = self.request.get('content')
        message = Message(author=user, content=content)
        message.put()
        self.redirect('/')

class DeleteHandler(webapp.RequestHandler):
    def post(self):
        key = self.request.get('key')
        query = db.get(key)
        db.delete(query)
        self.response.out.write('message_%s' % key)

class LogoutHandler(webapp.RequestHandler):
    def get(self):
        self.redirect(users.create_logout_url('/'))

class QueryHandler(webapp.RequestHandler):
    def get(self):
        fp = urllib2.urlopen('http://www.google.com/ig/api?weather=%s' % (
            self.request.get('city')
        ))
        self.response.out.write(fp.read())

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/send', SendHandler),
        ('/delete', DeleteHandler),
        ('/logout', LogoutHandler),
        ('/query', QueryHandler),
        ], debug=True
    )
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
