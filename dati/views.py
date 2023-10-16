import logging
logging.basicConfig(level=logging.INFO)
from pathlib import Path


from django.shortcuts import render
from .models import *
from .forms import *
from rest_framework import status
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from django.db.models import Sum, Max, Count
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from django.utils import timezone


from rest_framework.response import Response

# https://manojadhikari.medium.com/track-email-opened-status-django-rest-framework-5fcd1fbdecfb
from rest_framework.views import APIView
from PIL import Image
from django.contrib.sessions.models import Session

BASE_DIR = Path(__file__).resolve().parent.parent
#print('BASE_DIR:',BASE_DIR)

def get_env_variable(env_name):
    #LogEntry.objects.create(key='BASE_DIR', value=BASE_DIR)
    if 'media' in str(BASE_DIR):
        session_cookie_name = 's_key_prod'
        subdomain = 'media'
    else:
        session_cookie_name = 's_key'
        subdomain = 'statsdev'
    if env_name == 'cookie name':
        returned_param = session_cookie_name
    elif env_name == 'subdomain':
        returned_param = subdomain
    else:
        returned_param = 'Error. env_name not matching.'
    return returned_param


# Create your views here.
def index(request):
    # Generate counts of some of the main objects
    num_email_clicks = Click.objects.all().count()
    context = {
        'num_email_clicks': num_email_clicks,
    }
    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.authtoken.models import Token

@csrf_exempt
def get_auth_token(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return JsonResponse({'token': token.key})
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

from django.contrib.auth import authenticate, login
from django.http import JsonResponse

def login_view(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid credentials'})

from django.urls import reverse
import re

#html_detail, redirect_instances = render_with_redirect(mail_template, set(), email, context_data, target_user)

def render_with_redirect(mail_template, redirect_set, email, context_data, target_user):
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    """
    Renders the provided mail_template, replacing links with redirect URLs.
    Returns a tuple containing the rendered HTML and a set of new Redirect instances created.
    """
    html_detail = mail_template.render(context_data)
    redirect_instances = set()

    def replace_link(match):
        url = match.group(1)
        #print("Matched URL:", url)
        LogEntry.objects.create(key='Matched URL', value=url)
        existing_redirect = next((r for r in redirect_set if r.target_url == url), None)
        if existing_redirect:
            redirect_code = existing_redirect.redirect_code
        else:
            redirect_code = Redirect.objects.aggregate(Max('redirect_code'))['redirect_code__max'] or 1
            redirect_code += 1
            try:
                target_wpid = WPID.objects.get(link = url)
            except:
                target_wpid = WPID.objects.get(link = 'https://dundlabumi.lv/index.php/products/')
            redirect = Redirect.objects.create(redirect_code=redirect_code, target_url=url, wpid=target_wpid, usermodel=target_user)
            if email is not None:
                redirect.outbound_email = email
                redirect.save()
            redirect_instances.add(redirect)
            redirect_set.add(redirect)
            LogEntry.objects.create(key='target_wpid.wp_id', value=target_wpid.wp_id)

        subdomain = get_env_variable('subdomain')
        redirect_url = reverse('link', args=[redirect_code])
        LogEntry.objects.create(key='redirect_url', value=redirect_url)
        return f'<a href="https://'+subdomain+'.dundlabumi.lv'+redirect_url+'" rel="nofollow noreferrer"'

    pattern = r'<a href="(https?://[^"]+)"'
    html_detail = re.sub(pattern, replace_link, html_detail)

    return html_detail, redirect_instances

def email_viewed(request, email_id):
    # update the email record to indicate that it was viewed
    email = OutboundEmail.objects.get(id=email_id)
    email.status = True
    email.save()

    # return a blank image to display in the email
    image_data = open("blank.png", "rb").read()
    return HttpResponse(image_data, content_type="image/png")

# https://manojadhikari.medium.com/track-email-opened-status-django-rest-framework-5fcd1fbdecfb
class SendTemplateMailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get params from API call:
        target_user_email = request.data.get('recipient_email')
        subject = request.data.get('subject')
        template_name = request.data.get('template_name')
        target_user = UserModel.objects.get(email=target_user_email)
        LogEntry.objects.create(key="target_user_email", value=target_user_email)
        LogEntry.objects.create(key="subject", value=subject)
        LogEntry.objects.create(key="template_name", value=template_name)

        from_email = 'jaunumi@dundlabumi.lv'
        to = [target_user_email]
        mail_template = get_template(template_name)

        email = OutboundEmail.objects.create(recipient=target_user_email, subject=subject, status=False,
                                             usermodel=target_user, template_name=template_name)
        #LogEntry.objects.create(key="email", value=email)
        context_data = dict()
        context_data["image_url"] = request.build_absolute_uri(("send/render_image2/")) + str(email.id)
        #LogEntry.objects.create(key='context_data["image_url"]', value=context_data["image_url"])
        context_data["cid"] = email.id
        #LogEntry.objects.create(key='context_data["cid"]', value=context_data["cid"])
        context_data["url_is"] = context_data["image_url"]
        #LogEntry.objects.create(key='context_data["url_is"]', value=context_data["url_is"])

        # render the email body with redirect links
        html_detail_redirects, redirect_instances = render_with_redirect(mail_template, set(), email, context_data, target_user)
        #LogEntry.objects.create(key='html_detail', value=html_detail)
        #LogEntry.objects.create(key='redirect_instances', value=redirect_instances)

        email.body=html_detail_redirects
        email.save()

        msg = EmailMultiAlternatives(subject, html_detail_redirects, from_email, to)
        msg.content_subtype = 'html'
        #LogEntry.objects.create(key='msg', value=msg)
        msg_result = msg.send()
        LogEntry.objects.create(key='msg_result', value=msg_result)

        response_dict = {
            'target_user_email': target_user_email,
            'email_id': email.id,
            'template_name': template_name,
            'msg_result': msg_result,
            'success': True,
        }
        LogEntry.objects.create(key='response_dict', value=response_dict)
        return Response(response_dict)

class SendTemplateMailTestView(APIView):
    def post(self, request, *args, **kwargs):
        # Get params from API call:
        target_user_email = request.data.get('recipient_email')
        subject = request.data.get('subject')
        LogEntry.objects.create(key="django_view", value="SendTemplateMailTestView")
        LogEntry.objects.create(key="target_user_email", value=target_user_email)
        LogEntry.objects.create(key="subject", value=subject)

        from_email = 'jaunumi@dundlabumi.lv'
        to = [target_user_email]
        mail_template = get_template('mail_template.html')

        context_data_is = dict()
        context_data_is["image_url"] = request.build_absolute_uri(("render_image"))
        url_is = context_data_is["image_url"]
        context_data_is['url_is'] = url_is
        html_detail = mail_template.render(context_data_is)
        from_email = 'jaunumi@dundlabumi.lv'
        to = [target_user_email]

        msg = EmailMultiAlternatives(subject, html_detail, from_email, to)
        msg.content_subtype = 'html'
        msg_result = msg.send()
        response_dict = {
            'target_user_email': target_user_email,
            'msg_result': msg_result,
            'success': True,
        }
        LogEntry.objects.create(key='response_dict', value=response_dict)
        return Response(response_dict)


from django.http import HttpResponse
from django.shortcuts import get_object_or_404

def render_image2(request, id):
    # Get the email by the ID
    email = OutboundEmail.objects.get(id=id)
    email.status = True
    email.save()

    # Get the UserModel for the email address
    email_recipient = UserModel.objects.get(email=email.recipient)

    # Check if a session_key is associated with this user.
    if email_recipient.sessions.exists():
        session_values = email_recipient.sessions.all()
        # Now get the last session_key and use that.
        for session in session_values:
            session_key = session.session_key
        # Set the current session_key in case it differs.
        request.session['session_key'] = session_key
        request.session.save()
    else:
        # The session_key has not been saved.
        # Check if there is a cookie that provides a session_key
        if 'session_key' in request.session:
            session_key = request.session['session_key']
        if 'session_key' not in request.session or session_key == None:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                request.session.save()
                session_key = request.session.session_key
        if Session.objects.filter(session_key=session_key).exists():
            session = Session.objects.get(session_key=session_key)
        else:
            session = Session.objects.create(session_key=session_key)
        # Add the session to the UserModel
        email_recipient.session = session
        email_recipient.save()

    image = Image.new('RGB', (1, 1), (255, 255, 255))
    response = HttpResponse(content_type="image/png", status=status.HTTP_200_OK)
    image.save(response, "PNG")

    session_cookie_name = get_env_variable('cookie name')

    response.set_cookie(session_cookie_name, session_key)

    return response

import base64
import hashlib

def get_user_id_from_wordpress_cookie(cookie):
    if not cookie:
        return None

    cookie_name = 'wordpress_logged_in_'
    start_index = cookie.find(cookie_name)
    if start_index == -1:
        return None

    end_index = cookie.find(';', start_index)
    if end_index == -1:
        end_index = len(cookie)

    cookie_value = cookie[start_index:end_index]
    cookie_parts = cookie_value.split('|')
    if len(cookie_parts) != 3:
        return None

    user_data = cookie_parts[1]
    user_data_decoded = base64.b64decode(user_data + '==')
    md5_hash = hashlib.md5(cookie_value.encode('utf-8') + 'salt'.encode('utf-8')).hexdigest()
    sha_hash = hashlib.sha256(cookie_value.encode('utf-8') + md5_hash.encode('utf-8')).hexdigest()

    if sha_hash != cookie_parts[2]:
        return None

    user_data_parts = user_data_decoded.decode('utf-8').split(':')
    if len(user_data_parts) != 2:
        return None

    user_id = int(user_data_parts[0])

    return user_id

def get_session_and_usermodel2(request):
    temp_message = ""
    session_cookie_name = get_env_variable('cookie name')
    #LogEntry.objects.create(key='session_cookie', value=session_cookie_name)
    if not session_cookie_name in request.session:
        LogEntry.objects.create(key='session_cookie_name cookie not found in request', value="")
        request.session.create()
        request.session.save()
        session_key = request.session.session_key
        # Save the session to s_key
        request.session[session_cookie_name] = session_key
        request.session.save()
    else:
        LogEntry.objects.create(key='session_cookie_name cookie present in request', value="")
        session_key = request.session[session_cookie_name]
    if Session.objects.filter(session_key=session_key).exists():
        session = Session.objects.get(session_key=session_key)
    else:
        expire_date = timezone.now() + timezone.timedelta(days=360)
        session = Session.objects.create(session_key=session_key, expire_date=expire_date)

    print('session_key:', session_key)
    LogEntry.objects.create(key='session_key', value=session_key)

    # Check if the session points to an existing user. If not, need to create and associate a usermodel
    usermodels_for_current_session = session.usermodels.all()
    if not usermodels_for_current_session:
        # No usermodel is associated with this session. Create one.
        usermodel = UserModel.objects.create()
        usermodel.sessions.add(session)
        usermodel.save()
        usermodels_for_current_session = [usermodel]
    else:
        usermodel = usermodels_for_current_session[0]
    LogEntry.objects.create(key='usermodel', value=usermodel.id)

    # Get the user_id if it was passed from Wordpress.
    uid = request.GET.get('user_id')
    if uid is not None and str(uid) != '0':
        LogEntry.objects.create(key='uid', value=uid)
    else:
        LogEntry.objects.create(key='uid', value="")

    # We now have a session with session_key and a linked usermodel instance.

    if uid is not None and str(uid) != '0':
        # A Wordpress user_id is known for this usermodel.
        # Check if this usermodel already associated with a wp_user_id:
        #LogEntry.objects.create(key='uid exists', value="")

        # Check if a UserModel is associated with this uid.
        if UserModel.objects.filter(wp_user_id=uid).exists():
            usermodel = UserModel.objects.get(wp_user_id=uid)
            LogEntry.objects.create(key='usermodel.id associated with uid', value=usermodel.id)
            # Check that the session points to the usermodel that is associated with the wp_user_id.
            if usermodels_for_current_session[0].id != usermodel.id:
                # The session is pointing to a different usermodel record, not the one associated with the uid.
                old_usermodel = usermodels_for_current_session[0]
                # Delete this record and associate the session with the existing usermodel that
                LogEntry.objects.create(key='Deleting usermodel record as wp_user is saved in different record. Deleting usermodel.id:', value=usermodels_for_current_session[0].id)

                # Get UserPageviews for old_usermodel and usermodel.
                old_userpageviews = UserPageview.objects.filter(user_model=old_usermodel)
                for old_pageview in old_userpageviews:
                    LogEntry.objects.create(key="Evaluating user's pageview for wpid:",value = old_pageview.wpid)
                    if UserPageview.objects.filter(user_model=usermodel, wpid=old_pageview.wpid).exists():
                        remaining_userpageview = UserPageview.objects.get(user_model=usermodel, wpid=old_pageview.wpid)
                        remaining_userpageview.aged_score += old_pageview.aged_score
                        LogEntry.objects.create(key="Adding aged_score to usermodel's userpageview aged_score. remaining_userpageview:",value=remaining_userpageview.id)
                        remaining_userpageview.save()
                        old_pageview.delete()
                    else:
                        old_pageview.user_model=usermodel
                        old_pageview.save()
                        LogEntry.objects.create(key="Changed userpageview to logged in usermodel. old_userpageview:",value = old_pageview.id)

                # Get UserTags for old_usermodel and usermodel.
                old_usertags = UserTag.objects.filter(user_model=old_usermodel)
                for old_tag in old_usertags:
                    LogEntry.objects.create(key="Evaluating user's tag for tag_id:", value=old_tag.tag_id)
                    if UserTag.objects.filter(user_model=usermodel, tag=old_tag.tag_id).exists():
                        remaining_usertag = UserTag.objects.get(user_model=usermodel,
                                                                          tag=old_tag.tag_id)
                        remaining_usertag.aged_score += old_tag.aged_score
                        LogEntry.objects.create(
                            key="Adding aged_score to usermodel's usertag aged_score. remaining_usertag:",
                            value=remaining_usertag.id)
                        remaining_usertag.save()
                        old_tag.delete()
                    else:
                        old_tag.user_model = usermodel
                        old_tag.save()
                        LogEntry.objects.create(
                            key="Changed userlink to logged in usermodel. old_tag:",
                            value=old_tag.id)

                usermodel.sessions.add(session)
                old_usermodel.delete()
                usermodel.save()
        else:
            # usermodel is not yet associated with the wp_user_id
            # Check that we have a User record imported from dundlabumi.lv
            user = User.objects.filter(id=uid)
            if len(user) > 0:
                # Retrieve values to update UserModel record
                user = User.objects.get(id=uid)
                logged_in_username = user.username
                logged_in_user_email = user.email
                LogEntry.objects.create(key='logged_in_user_email', value=logged_in_user_email)
                usermodel.email = logged_in_user_email
                usermodel.username = logged_in_username
            else:
                LogEntry.objects.create(key='No user record was found with id=uid', value="")
            # Update the wp_user_id field even if the User record did not exist.
            usermodel.wp_user_id = uid
            usermodel.save()
            LogEntry.objects.create(key='usermodel.wp_user_id', value=usermodel.wp_user_id)
    return session, usermodel

def page(request, id):
    # Get the session from the received request
    temp_message=""
    session, usermodel = get_session_and_usermodel2(request)
    print('usermodel.id:', usermodel.id)

    image = Image.new('RGB', (1, 1), (255, 255, 255))
    response = HttpResponse(content_type="image/png", status=status.HTTP_200_OK)
    image.save(response, "PNG")

    wpid=WPID.objects.get(wp_id=id)
    pageview = Pageview.objects.create(wpid=wpid, session=session, temp_message=temp_message)
    LogEntry.objects.create(key='Page view registered. ID:', value=pageview.id)
    LogEntry.objects.create(key='Viewed page title:', value=wpid.name)
    LogEntry.objects.create(key='Page view occured. WPID:', value=id)
    # Now increment the User / Pageview relevance score.
    existing_userpageviews = UserPageview.objects.filter(user_model=usermodel, wpid=wpid)
    if existing_userpageviews.exists():
        # Already have a relevance score for this page for a specific session, so it has been clicked in the last 2 years from this session_key
        user_page = existing_userpageviews.first()
        # Increment aged score by 1 as new pageview today.
        aged_score = user_page.aged_score
        user_page.aged_score = aged_score + 1
        if user_page.user_model is None:
            if usermodel is not None:
                # Session known, no username associated with the session, but we know the user.
                user_page.user_model = usermodel
        user_page.save()
    else:
        # No relevance score for a usermodel or this session_key so link not clicked in last 2 years.
        #if UserPageview.objects.exists():
        #    max_id = UserPageview.objects.aggregate(max_id=Max('id'))['max_id']
            #new_id = max_id + 1
        #else:
            #new_id = 1
        #UserPageview.objects.create(user_model=usermodel,wpid=wpid, aged_score=1, id=new_id)
        UserPageview.objects.create(user_model=usermodel, wpid=wpid, aged_score=1)

    # Check if the wpid refers to a product. If so, update UserTags.
    if wpid.post_type == 'product':
        # Retrieve all the tags associated with the given WPID instance
        wpid_tags = wpid.tags.all()

        # Iterate over each tag instance
        for tag in wpid_tags:
            # Check if an instance of UserTag exists for this tag and UserModel
            LogEntry.objects.create(key='Tag name:', value=tag)
            user_tag = UserTag.objects.filter(tag=tag, user_model=usermodel)
            #LogEntry.objects.create(key='len(user_tag):', value=len(user_tag))
            created = False
            if len(user_tag) == 0:
                #LogEntry.objects.create(key='len(user_tag) == 0', value='')
                #if UserTag.objects.exists():
                #    max_id = UserTag.objects.aggregate(max_id=Max('id'))['max_id']
                #    new_id = max_id + 1
                #else:
                #    new_id = 1
                #user_tag = UserTag.objects.create(tag=tag, user_model=usermodel, aged_score=1, id=new_id)
                user_tag = UserTag.objects.create(tag=tag, user_model=usermodel, aged_score=1)
                created = True
                user_tag.save()
            else:
                #LogEntry.objects.create(key='len(user_tag) != 0', value='')
                user_tag = user_tag[0]
            #user_tag, created = UserTag.objects.get_or_create(tag=tag, user_model=usermodel, defaults={'aged_score': 1})

            # Increment the aged_score if the instance already exists
            if not created:
                user_tag.aged_score += 1
                user_tag.save()
                LogEntry.objects.create(key='Existing UserTag incremented. tag_id:', value=user_tag.tag_id)
                LogEntry.objects.create(key='New aged_score:', value=user_tag.aged_score)
            else:
                LogEntry.objects.create(key='New UserTag registered. ID:', value=user_tag.id)
    else:
        LogEntry.objects.create(key='Skipping UserTag registration as WPID is not a product', value=0)
    return response

def non_product_page(request, id):
    # Get the session from the received request
    temp_message=""
    session, usermodel = get_session_and_usermodel2(request)
    print('usermodel.id:', usermodel.id)

    image = Image.new('RGB', (1, 1), (255, 255, 255))
    response = HttpResponse(content_type="image/png", status=status.HTTP_200_OK)
    image.save(response, "PNG")

    wpid=WPID.objects.get(wp_id=id)
    pageview = Pageview.objects.create(wpid=wpid, session=session, temp_message=temp_message)
    LogEntry.objects.create(key='Page view registered. ID:', value=pageview.id)
    LogEntry.objects.create(key='Viewed page title:', value=wpid.name)
    LogEntry.objects.create(key='Page view occured. WPID:', value=id)
    # Now increment the User / Pageview relevance score.
    existing_userpageviews = UserPageview.objects.filter(user_model=usermodel, wpid=wpid)
    if existing_userpageviews.exists():
        # Already have a relevance score for this page for a specific session, so it has been clicked in the last 2 years from this session_key
        user_page = existing_userpageviews.first()
        # Increment aged score by 1 as new pageview today.
        aged_score = user_page.aged_score
        user_page.aged_score = aged_score + 1
        if user_page.user_model is None:
            if usermodel is not None:
                # Session known, no username associated with the session, but we know the user.
                user_page.user_model = usermodel
        user_page.save()
    else:
        # No relevance score for a usermodel or this session_key so link not clicked in last 2 years.
        #if UserPageview.objects.exists():
        #    max_id = UserPageview.objects.aggregate(max_id=Max('id'))['max_id']
            #new_id = max_id + 1
        #else:
            #new_id = 1
        #UserPageview.objects.create(user_model=usermodel,wpid=wpid, aged_score=1, id=new_id)
        UserPageview.objects.create(user_model=usermodel, wpid=wpid, aged_score=1)
    return response

from django.shortcuts import redirect

def link(request, id):
    temp_message = ""
    redirect_usermodel = None
    # Read data about the link that brought the user to the site.
    if not Redirect.objects.filter(redirect_code=id).exists():
        # The redirect code does not exist in the database. Push user to the shop page instead.
        target_url = 'https://dundlabumi.lv/index.php/veikals/'
        response = redirect(target_url)
    else:
        # A valid redirect code was received.
        redirect_record = Redirect.objects.get(redirect_code=id)

        target_url = redirect_record.target_url
        wpid_of_linked_page = redirect_record.wpid_id
        redirect_usermodel = redirect_record.usermodel

        LogEntry.objects.create(key='Link click occured. Redirect code:', value=id)
        session, usermodel = get_session_and_usermodel2(request)
        print('usermodel.id:', usermodel.id)

        link_click = Click.objects.create(redirect_code=redirect_record, session=session, temp_message=temp_message)
        LogEntry.objects.create(key='Link click registered in dati_click. ID:', value=link_click.id)
        # If the session usermodel is not the same as the redirect link usermodel, change the usermodel to that of the redirect link.
        if redirect_usermodel is not None:
            if usermodel.id != redirect_usermodel.id:
                # Users not the same. Change the session to point to the redirect user.

                # Update UserPageView instances where user_model = usermodel
                UserPageview.objects.filter(user_model=usermodel).update(user_model=redirect_usermodel)

                # Update UserLink instances where user_model = usermodel
                UserLink.objects.filter(user_model=usermodel).update(user_model=redirect_usermodel)

                # Update UserTag instances where user_model = usermodel
                UserTag.objects.filter(user_model=usermodel).update(user_model=redirect_usermodel)

                # Delete the current usermodel
                usermodel.delete()
                redirect_usermodel.sessions.add(session)
                redirect_usermodel.save()
                usermodel = redirect_usermodel
                LogEntry.objects.create(key='Usermodel changed to usermodel of redirect link:', value=usermodel.id)

        # Create the response to return to the user.
        response = redirect(target_url)
        # Now increment the User / Link relevance score.
        if WPID.objects.filter(wp_id=wpid_of_linked_page).exists():
            clicked_wpid = WPID.objects.get(wp_id=wpid_of_linked_page)
            try:
                user_link = UserLink.objects.get(user_model=usermodel, wpid=clicked_wpid)
            except UserLink.DoesNotExist:
                # No relevance score for a usermodel or this session_key so link not clicked in last 2 years.
                #if UserLink.objects.exists():
                #    max_id = UserLink.objects.aggregate(max_id=Max('id'))['max_id']
                #    new_id = max_id + 1
                #else:
                #    new_id = 1
                #user_link = UserLink.objects.create(user_model=usermodel, wpid=clicked_wpid, aged_score=1, id=new_id)
                user_link = UserLink.objects.create(user_model=usermodel, wpid=clicked_wpid, aged_score=1)
                LogEntry.objects.create(key='New UserLink record created in dati_userlink. New aged_score:', value=1)
            else:
                # Already have a relevance score for this link for a specific usermodel, so it has been clicked in the last 2 years from this session_key
                user_link.aged_score += 1
                user_link.save()
                LogEntry.objects.create(key='UserLink exists in dati_userlink. New aged_score:',
                                        value=user_link.aged_score)
    return redirect(target_url, response=response)

from .forms import UserForm

# View to show list of users that have read emails
def email_readers(request):
    # Filter the outbound emails with status = 1 meaning the email has been read.
    # Get the list of usermodel values that are in the list of read outbound emails.
    # Sort the list of readers in decending order by number of emails read.
    # Retrieve clicks for each user.
    read_emails = OutboundEmail.objects.filter(status=1)
    # Create a list of users that have read emails
    readers = {}
    reader_usermodels = {}
    reader_clicks_dict = {}
    for email in read_emails:
        reader = email.recipient
        #reader_usermodel = email.usermodel
        if reader not in readers.keys():
            readers[reader]={}
            user_instance = UserModel.objects.get(email=reader)
            readers[reader]['UserModel_instance'] = user_instance
            readers[reader]['UserModel_id'] = user_instance.id
            #sessions_list = user_instance.sessions.values_list('session_key', flat=True)
            # Retrieve the values of the sessions
            #sessions_values = Session.objects.filter(session_key__in=sessions_list).values_list('session_key', flat=True)
            #readers[reader]['session_list'] = sessions_values
            #reader_usermodels[reader_usermodel] = sessions_values
        #reader_clicks = Click.objects.filter(session__in=sessions_values)
        #readers[reader]['clicks'] = reader_clicks
        my_dict={}
        my_dict['key']='value'


    context = {'readers' : readers,
               'my_dict' : my_dict,
    }
    return render(request, 'readers.html', context=context)



def user_details(request, user_id):
    try:
        user = UserModel.objects.get(id=user_id)
    except:
        return HttpResponse("User not found", status=404)

    pageviews = UserPageview.objects.filter(user_model=user)
    page_labels = []
    page_values = []

    page_scores_dict = {}
    for pageview in pageviews:
        wpid_name = pageview.wpid.name
        aged_score = pageview.aged_score
        if wpid_name in page_scores_dict:
            page_scores_dict[wpid_name] += aged_score
        else:
            page_scores_dict[wpid_name] = aged_score

    page_scores = [(wpid_name, aged_score) for wpid_name, aged_score in page_scores_dict.items()]
    page_scores = sorted(page_scores, key=lambda x: x[1], reverse=True)
    for page in page_scores:
        page_labels.append(page[0])
        page_values.append(page[1])

    tags = UserTag.objects.filter(user_model=user)
    tag_labels=[]
    tag_values=[]
    tag_scores_dict = {}
    for tag in tags:
        tag_name = tag.tag.tag_name
        aged_score = tag.aged_score
        if tag_name in tag_scores_dict:
            tag_scores_dict[tag_name] += aged_score
        else:
            tag_scores_dict[tag_name] = aged_score

    tag_scores = [(tag_name, aged_score) for tag_name, aged_score in tag_scores_dict.items()]
    tag_scores = sorted(tag_scores, key=lambda x: x[1], reverse=True)
    for tag in tag_scores:
        tag_labels.append(tag[0])
        tag_values.append(tag[1])

    return render(request, 'user_view.html', {'user': user, 'page_scores': page_scores, 'tag_scores': tag_scores,
                                              'tag_labels' : tag_labels, 'tag_values' : tag_values,
                                              'page_labels' : page_labels, 'page_values' : page_values})

# List of users sorted by total aged_score, and showing items viewed.
from django.core.paginator import Paginator

def user_list(request):
    user_list = UserModel.objects.annotate(total_aged_score=Sum('pageviews__aged_score')).order_by('-total_aged_score')

    paginator = Paginator(user_list, 20)  # Display 20 users per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}
    return render(request, 'user_list.html', context)

def named_user_list(request):
    user_list = UserModel.objects.filter(email__isnull=False, email__gt='').annotate(total_aged_score=Sum('pageviews__aged_score')).order_by('-total_aged_score')

    paginator = Paginator(user_list, 20)  # Display 20 users per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}
    return render(request, 'named_user_list.html', context)

def redirect_details(request):
    if request.method == 'POST':
        form = RedirectCodeForm(request.POST)
        if form.is_valid():
            redirect_code = form.cleaned_data['redirect_code']
            try:
                redirect = Redirect.objects.get(redirect_code=redirect_code)
                clicks = Click.objects.filter(redirect_code=redirect)
                click_id_list = list(clicks.values_list('id', flat=True))

                earliest_click_dt = clicks.earliest('click_dt').click_dt

                user_pageviews = Pageview.objects.filter(
                    session_id__in=clicks.values_list('session_id', flat=True),  # Filter based on session_id
                    view_dt__gt=earliest_click_dt
                ).select_related('wpid')

                user_pageview_dict = {}
                pageview_id_list=[]
                for pageview in user_pageviews:
                    pageview_id_list.append(pageview.id)
                    for user_model in pageview.session.usermodels.all():  # Iterate over related usermodels
                        user_id = user_model.id
                        if user_id not in user_pageview_dict:
                            user_pageview_dict[user_id] = {
                                'user': user_model,
                                'pageviews': []
                            }
                        user_pageview_dict[user_id]['pageviews'].append(pageview)

                context = {
                    'redirect_code': redirect_code,
                    'click_id_list': click_id_list,
                    'earliest_click_dt': earliest_click_dt,
                    'redirect': redirect,
                    'pageview_id_list' : pageview_id_list,
                    'user_pageview_dict': user_pageview_dict.values(),
                }
                return render(request, 'redirects_to_pageviews.html', context)
            except Redirect.DoesNotExist:
                error_message = 'Redirect code not found.'
        else:
            error_message = 'Invalid form input.'
    else:
        form = RedirectCodeForm()
        error_message = None

    context = {
        'form': form,
        'error_message': error_message,
    }
    return render(request, 'redirects_to_pageviews.html', context)

def redirect_product_details(request):
    if request.method == 'POST':
        form = RedirectCodeForm(request.POST)
        if form.is_valid():
            redirect_code = form.cleaned_data['redirect_code']
            try:
                redirect = Redirect.objects.get(redirect_code=redirect_code)
                clicks = Click.objects.filter(redirect_code=redirect)
                click_id_list = list(clicks.values_list('id', flat=True))

                earliest_click_dt = clicks.earliest('click_dt').click_dt

                pageviews = Pageview.objects.filter(
                    session_id__in=clicks.values_list('session_id', flat=True),  # Filter based on session_id
                    view_dt__gt=earliest_click_dt
                ).select_related('wpid')

                wpid_pageview_dict = {}
                pageview_id_list = []
                for pageview in pageviews:
                    pageview_id_list.append(pageview.id)
                    wpid = pageview.wpid_id
                    if wpid not in wpid_pageview_dict:
                        wpid_pageview_dict[wpid] = {
                            'wpid': pageview.wpid,
                            'pageviews': []
                        }
                    wpid_pageview_dict[wpid]['pageviews'].append(pageview)

                context = {
                    'redirect_code': redirect_code,
                    'click_id_list': click_id_list,
                    'earliest_click_dt': earliest_click_dt,
                    'redirect': redirect,
                    'pageview_id_list': pageview_id_list,
                    'wpid_pageview_dict': wpid_pageview_dict.values(),
                }
                return render(request, 'redirects_to_pageviews_by_product.html', context)
            except Redirect.DoesNotExist:
                error_message = 'Redirect code not found.'
        else:
            error_message = 'Invalid form input.'
    else:
        form = RedirectCodeForm()
        error_message = None

    context = {
        'form': form,
        'error_message': error_message,
    }
    return render(request, 'redirects_to_pageviews_by_product.html', context)

def tag_count_bar_charts(request):
    tag_types = Tag.TAG_TYPES
    tag_counts_by_type = []

    total_pageviews = Pageview.objects.count()

    for tag_type in tag_types:
        tag_type_name = tag_type[1]
        tag_type_tags = Tag.objects.filter(tag_type=tag_type[0])
        tag_names = [tag.tag_name for tag in tag_type_tags]
        tag_type_counts = []

        for tag_name in tag_names:
            pageview_count = Pageview.objects.filter(wpid__tags__tag_name=tag_name).count()
            tag_type_counts.append((tag_name, (pageview_count / total_pageviews) * 100))

        sorted_tag_counts = sorted(tag_type_counts, key=lambda x: x[1], reverse=True)
        sorted_tag_names, sorted_tag_percentages = zip(*sorted_tag_counts)

        # Convert to lists
        sorted_tag_names = list(sorted_tag_names)
        sorted_tag_percentages = list(sorted_tag_percentages)

        tag_counts_by_type.append({
            'label': tag_type_name,
            'data': sorted_tag_percentages,
            'labels': sorted_tag_names,
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        })

    return render(request, 'tag_count_bar_charts.html', {
        'tag_counts_by_type': tag_counts_by_type
    })

from django.db.models import Count, F

def type_and_colour_bar_charts(request):
    garment_types = Tag.objects.filter(tag_type='2')  # Filter by Garment type

    tag_counts_by_garment_type = []

    for garment_type in garment_types:
        garment_type_name = garment_type.tag_name
        wpids_with_garment_type = WPID.objects.filter(tags=garment_type)

        # Filter only Color tags (tag_type='3')
        color_tags = Tag.objects.filter(tag_type='3')

        pageview_counts = Pageview.objects.filter(
            wpid__in=wpids_with_garment_type,
            wpid__tags__in=color_tags  # Filter only Color tags
        ).values('wpid__tags__tag_name') \
            .annotate(count=Count('wpid__tags__tag_name'))

        total_pageviews = Pageview.objects.count()

        tag_type_counts = []

        for pageview_count in pageview_counts:
            color_name = pageview_count['wpid__tags__tag_name']
            pageview_color_count = pageview_count['count']
            percentage = (pageview_color_count / total_pageviews) * 100
            tag_type_counts.append((color_name, percentage))

        if tag_type_counts:
            sorted_tag_counts = sorted(tag_type_counts, key=lambda x: x[1], reverse=True)
            sorted_tag_names, sorted_tag_percentages = zip(*sorted_tag_counts)

            # Convert to lists
            sorted_tag_names = list(sorted_tag_names)
            sorted_tag_percentages = list(sorted_tag_percentages)

            tag_counts_by_garment_type.append({
                'garment_type_name': garment_type_name,
                'data': sorted_tag_percentages,
                'labels': sorted_tag_names,
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            })

    return render(request, 'type_and_colour_bar_charts.html', {
        'tag_counts_by_garment_type': tag_counts_by_garment_type
    })
