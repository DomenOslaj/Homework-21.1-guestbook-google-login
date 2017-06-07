#!/usr/bin/env python
import os
import jinja2
import webapp2
from models import Message
from google.appengine.api import users



template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}

        # if we put google login here -> automatically in every handler
        user = users.get_current_user()
        params["user"] = user

        if user:
            logged_in = True
            logout_url = users.create_logout_url('/')
            params["logout_url"] = logout_url

        else:
            logged_in = False
            login_url = users.create_login_url('/')
            params["login_url"] = login_url

        params["logged_in"] = logged_in

        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))


class MainHandler(BaseHandler):
    def get(self):

        return self.render_template("main.html",)

class GuestbookHandler(BaseHandler):
    def get(self):
        messages = Message.query(Message.deleted == False).fetch()

        params = {"messages": messages}

        return self.render_template("guestbook.html", params=params)


    def post(self):
        user = users.get_current_user()

        if not user:
            return self.write("You are not logged in!")

        author = self.request.get("name")
        email = user.email()
        message = self.request.get("message")

        if not author:
            author = "Anonymous"

        if "<script>" in message:
            return self.write("Can`t hack me ! :)")      #one way to gight JS injection

        user_details = Message(name=author, email=email, message=message)     #other way is to write .... message=message.replace("<script>"," ")
        user_details.put()                      #save to database

        return self.redirect_to("guestbook-site")

class EditMessageHandler(BaseHandler):
    def get(self, message_id):

        if not users.is_current_user_admin():
            return self.write("You are not admin!")

        message = Message.get_by_id(int(message_id))
        params = {"message": message}

        return self.render_template("edit_message.html", params=params)

    def post(self, message_id):

        if not users.is_current_user_admin():
            return self.write("You are not admin!")

        message = Message.get_by_id(int(message_id))
        message_new = self.request.get("message")
        message.message = message_new
        message.put()

        return self.redirect_to("guestbook-site")

class DeleteMessageHandler(BaseHandler):
    def get(self, message_id):

        if not users.is_current_user_admin():
            return self.write("You are not admin!")

        message = Message.get_by_id(int(message_id))
        params = {"message": message}

        return self.render_template("delete_message.html", params=params)

    def post(self, message_id):

        if not users.is_current_user_admin():
            return self.write("You are not admin!")

        message = Message.get_by_id(int(message_id))
        message.deleted = True
        message.put()

        return self.redirect_to("guestbook-site")

class ShowDeletedMessagesHandler(BaseHandler):
    def get(self):

        if not users.is_current_user_admin():
            return self.write("You are not admin!")

        messages = Message.query(Message.deleted == True).fetch()

        params = {"messages": messages}

        return self.render_template("deleted_messages.html", params=params)

class CompleteMessageDeleteHandler(BaseHandler):
    def get(self, message_id):
        if not users.is_current_user_admin():
            return self.write("You are not admin!")

        message = Message.get_by_id(int(message_id))
        params = {"message": message}

        return self.render_template("complete_message_delete.html", params=params)


    def post(self, message_id):
        if not users.is_current_user_admin():
            return self.write("You are not admin!")

        message = Message.get_by_id(int(message_id))

        message.key.delete()  #complete delete message

        return self.redirect_to("deleted-messages")



app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route("/guestbook", GuestbookHandler, name="guestbook-site"),
    webapp2.Route("/message/<message_id:\d+>/edit", EditMessageHandler),
    webapp2.Route("/message/<message_id:\d+>/delete", DeleteMessageHandler),
    webapp2.Route("/deleted_messages", ShowDeletedMessagesHandler, name="deleted-messages"),
    webapp2.Route("/message/<message_id:\d+>/complete-delete", CompleteMessageDeleteHandler),
], debug=True)
