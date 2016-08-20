import logging
import os

import jinja2
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates'),
    extensions=['jinja2.ext.autoescape'], autoescape=True)


class Document(ndb.Model):
  user_id = ndb.StringProperty()
  created_timestamp = ndb.DateTimeProperty(auto_now_add=True)
  updated_timestamp = ndb.DateTimeProperty(auto_now=True)
  title = ndb.StringProperty(default='')
  content = ndb.StringProperty(default='')

  @classmethod
  def list(cls, user):
    return cls.query().filter(cls.user_id==user.user_id()).fetch()


class DocMetadata(object):
  title = ''
  doc_id = ''
  def __init__(self, title, doc_id):
    self.title = title
    self.doc_id = doc_id


class MainPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      self.redirect('/user')
      return
    else:
      login_url = users.create_login_url('/')
      greeting = '<a href="{}">Sign in</a>'.format(login_url)
    html = '<html><title>Simple Login</title><body>{}</body></html>'.format(
        greeting)
    self.response.write(html)


class UserPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    docs = Document.list(user)
    doc_metadatas = [DocMetadata(doc.title, doc.key.id()) for doc in docs]
    template = env.get_template('user.html')
    html = template.render(
        doc_metadatas=doc_metadatas, email=user.email(), name=user.nickname())
    self.response.headers['Content-Type'] = 'text/html'
    self.response.write(html)
  

class CreateHandler(webapp2.RequestHandler):
  def post(self):
    user = users.get_current_user()
    title = self.request.get('title')
    doc = Document(title=title, user_id=user.user_id())
    doc.put()
    self.redirect('/docs?docid=%s' % doc.key.id())

class EditorPage(webapp2.RequestHandler):
  def get(self):
    doc_id = self.request.get('docid')
    if not doc_id: return
    logging.info('Getting doc by ID: %s', doc_id)
    doc = Document.get_by_id(int(doc_id))
    if not doc: return
    title, content = doc.title, doc.content
    template = env.get_template('editor.html')
    html = template.render(title=title, content=content, doc_id=doc_id)
    self.response.headers['Content-Type'] = 'text/html'
    self.response.write(html)


class SaveHandler(webapp2.RequestHandler):
  def post(self):
    params = self.request.params.items();
    doc_id, content = 0, ''
    for param in params:
      if param[0] == 'docId':
        doc_id = int(param[1])
      elif param[0] == 'content':
        content = param[1]
    logging.info('Saving doc with ID: %s', doc_id);
    if not doc_id: return
    doc = Document.get_by_id(int(doc_id))
    doc.content = content
    doc.put()
    logging.info('Saved doc with ID: %s', doc_id);


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/user', UserPage),
    ('/docs', EditorPage),
    ('/create', CreateHandler),
    ('/save', SaveHandler),
], debug=True)
