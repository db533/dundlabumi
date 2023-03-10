from django.db import models

# Create your models here.
from django.db import models
from django.db.models.fields import CharField, EmailField, UUIDField
from django.contrib.sessions.models import Session
#from djongo.models.fields import ObjectIdField

class List(models.Model):
    list_id = models.IntegerField(default=0, help_text='The ID from the list in the Newsletter plugin')
    name = models.CharField(max_length=255, help_text='The name of the list in the Newsletter plugin')

    def __str__(self):
        return self.name

class UserModel(models.Model):
    subscriber_id = models.IntegerField(default=0, help_text='The subscriber ID from the Newsletter plugin', primary_key=True)
    email = EmailField(max_length=254, blank=True, null=True)
    lists = models.ManyToManyField(List, related_name='users')
    sessions = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=False,
                                      help_text='The list of session IDs associated with this user',
                                      verbose_name=('Session ID list'))

    def __str__(self):
        return self.email

class OutboundEmail(models.Model):
    recipient = models.EmailField()
    #subscriber = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, blank=False,
    #                                  help_text='The subscriber to whom the email was sent',
    #                                  verbose_name=('Email subscriber'), default=1)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sessions = models.ManyToManyField(Session)

    def __str__(self):
        return self.subject

class Tag(models.Model):
    tag_id = models.IntegerField(default=0, help_text='The ID of the tag in Woocommerce.', primary_key=True)
    tag_name = models.CharField(max_length=120, default="", help_text='Tag name.')

class WPID(models.Model):
    wp_id = models.IntegerField(default=0, help_text='The ID of the Wordpress record.', primary_key=True)
    post_type = models.CharField(max_length=20, default = "", help_text='Post type of the record.')
    name = models.CharField(max_length=120, default="", help_text='Name of the record.')
    tags = models.ManyToManyField(Tag, help_text='Tags associated with this WP id.', blank=True)

    def __str__(self):
        return self.name

class Redirect(models.Model):
    redirect_code = models.IntegerField(default=0, help_text='The ID to be used when calling this redirect.')
    target_url = models.CharField(max_length=255, help_text='The url to redirect to. Excludes the domain name.')
    wpid = models.ForeignKey(WPID, on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text='The Wordpress ID associated with this target_url',
                                 verbose_name=('WP id'))
    subscriber = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, blank=True,
                                      help_text='The subscriber to whom the link was sent',
                                      verbose_name=('Email subscriber'), default=1)

    def __str__(self):
        return str(self.redirect_code)

class Pageview(models.Model):
    page = models.IntegerField(default=0, help_text='The ID of the Wordpress page that was displayed.')
    view_dt = models.DateTimeField(auto_now=False, auto_now_add=True)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=False,
                                 help_text='The session associated with this pageview',
                                 verbose_name=('Session'))
    session_key = models.CharField(max_length=64, default="",
                                   help_text='The session id that was associated with this click.')
    temp_message = models.CharField(max_length=255)

    def __str__(self):
        return str(self.page)


class Click(models.Model):
    redirect_code = models.ForeignKey(Redirect, on_delete=models.SET_NULL, null=True, blank=False,
                                   help_text='Code that refers to a link that was clicked',
                                   verbose_name=('Redirect id code'))
    session_key = models.CharField(max_length=64, default = "", help_text='The session id that was associated with this click.')
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=False,
                                 help_text='The list of session IDs associated with this user',
                                 verbose_name=('Session ID list'))
    click_dt = models.DateTimeField(auto_now=False, auto_now_add=True)
    temp_message = models.CharField(max_length=255)

    def __str__(self):
        return self.id


class UserPageview(models.Model):
    # Model to store the current aged relevance score of a particular page for a particular user.
    user_model = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, blank=False,
                                 help_text='The user for whom this pageview relevance is being computed',
                                 verbose_name=('User'))
    wpid = models.ForeignKey(WPID, on_delete=models.SET_NULL, null=True, blank=False,
                                  help_text='The Wordpress ID for the page that was linked to.',
                                  verbose_name=('WP id'))
    aged_score = models.FloatField(help_text='Pageview relevance score',blank=False, verbose_name=('Skat??to lapu svar??gums'), default=0)

class UserLink(models.Model):
    # Model to store the current aged relevance score of a particular link click for a particular user.
    user_model = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, blank=False,
                                 help_text='The user for whom this link relevance is being computed',
                                 verbose_name=('User'))
    wpid = models.ForeignKey(WPID, on_delete=models.SET_NULL, null=True, blank=False,
                                  help_text='The Wordpress ID for the page that was linked to.',
                                  verbose_name=('WP id'))
    aged_score = models.FloatField(help_text='Link relevance score',blank=False, verbose_name=('Atv??rt?? linka svar??gums'), default=0)

