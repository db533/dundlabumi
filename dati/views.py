import logging
logging.basicConfig(level=logging.INFO)

from django.shortcuts import render
from .models import *
from rest_framework import status
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from django.utils import timezone


from rest_framework.response import Response

# https://manojadhikari.medium.com/track-email-opened-status-django-rest-framework-5fcd1fbdecfb
from rest_framework.views import APIView
from PIL import Image
from django.contrib.sessions.models import Session

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


from bs4 import BeautifulSoup
from django.urls import reverse
import re
from django.db.models import Max

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
        print("Matched URL:", url)
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

        redirect_url = reverse('link', args=[redirect_code])
        LogEntry.objects.create(key='redirect_url', value=redirect_url)
        return f'<a href="https://statsdev.dundlabumi.lv{redirect_url}" rel="nofollow noreferrer"'

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
        LogEntry.objects.create(key="target_user.subscriber_id", value=target_user.subscriber_id)

        from_email = 'jaunumi@dundlabumi.lv'
        to = [target_user_email]
        mail_template = get_template(template_name)

        email = OutboundEmail.objects.create(recipient=target_user_email, subject=subject, status=False,
                                             usermodel=target_user, template_name=template_name)
        LogEntry.objects.create(key="email", value=email)
        context_data = dict()
        context_data["image_url"] = request.build_absolute_uri(("send/render_image2/")) + str(email.id)
        LogEntry.objects.create(key='context_data["image_url"]', value=context_data["image_url"])
        context_data["cid"] = email.id
        LogEntry.objects.create(key='context_data["cid"]', value=context_data["cid"])
        context_data["url_is"] = context_data["image_url"]
        LogEntry.objects.create(key='context_data["url_is"]', value=context_data["url_is"])

        # render the email body with redirect links
        html_detail, redirect_instances = render_with_redirect(mail_template, set(), email, context_data, target_user)
        #LogEntry.objects.create(key='html_detail', value=html_detail)
        LogEntry.objects.create(key='redirect_instances', value=redirect_instances)

        email.body=html_detail
        email.save()

        msg = EmailMultiAlternatives(subject, html_detail, from_email, to)
        msg.content_subtype = 'html'
        LogEntry.objects.create(key='msg', value=msg)
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

    response.set_cookie('s_key', session_key)
    response.set_cookie('s_id', email_recipient.subscriber_id)

    return response

def page(request, id):
    # Get the session from the received request
    temp_message=""
    # Get the session from the received request
    #temp_message += "request.COOKIES: "+str(request.COOKIES)+" "
    if 's_key' in request.session:
        # A session key is stored in s_key.
        session_key = request.session['s_key']
        temp_message += "s_key present in request.session. "
        # Change the session key to the store value from the cookie.
    if not 's_key' in request.session or session_key == None:
        temp_message += "s_key missing or None. "
        request.session.create()
        request.session.save()
        session_key = request.session.session_key
        # Save the session to s_key
        request.session['s_key'] = session_key
        request.session.save()
    if Session.objects.filter(session_key=session_key).exists():
        session = Session.objects.get(session_key=session_key)
    else:
        expire_date = timezone.now() + timezone.timedelta(days=30)
        session = Session.objects.create(session_key=session_key, expire_date=expire_date)
    # Find the usermodels for the current session.
    usermodels_for_session = session.usermodels.all()


    # Check for a logged in user.
    session_data = session.get_decoded()
    uid = session_data.get('_auth_user_id')
    if uid is not None:
        user = User.objects.get(id=uid)
        logged_in_username = user.username
        temp_message += " username = " + str(logged_in_username)
        logged_in_user_email = user.email
        temp_message += " user_email = " + str(logged_in_user_email)

        # Check if this usermodel already exists, if not create:
        if not UserModel.objects.filter(username=logged_in_username).exists():
            usermodel = UserModel.objects.create(username=logged_in_username, email=logged_in_user_email)
            temp_message += " created usermodel as did not exist."
        else:
            usermodel = UserModel.objects.get(username=logged_in_username)
            temp_message += " retrieved existing usermodel."

        if usermodel not in usermodels_for_session:
            # This usermodel needs to be conencted to this session.
            usermodel.sessions.add(session)
            usermodel.save()
    else:
        # No logged in user, so username not known.
        # Get the usermodel for this session. Create if it is not associated.
        if len(usermodels_for_session) > 0:
            # A usermodel instance was found for the current session key.
            usermodel = UserModel.objects.get(sessions=session)
            temp_message += " retrieved usermodel. "
        else:
            # No usermodel exists for this session key. Create one and add the current session.
            usermodel = UserModel.objects.create()
            usermodel.sessions.add(session)
            usermodel.save()
            temp_message += " created usermodel "

    image = Image.new('RGB', (1, 1), (255, 255, 255))
    response = HttpResponse(content_type="image/png", status=status.HTTP_200_OK)
    image.save(response, "PNG")


    wpid=WPID.objects.get(wp_id=id)
    pageview = Pageview.objects.create(wpid=wpid, session=session, temp_message=temp_message)

    # Now increment the User / Pageview relevance score.
    existing_userpageviews = UserPageview.objects.filter(session=session, wpid=wpid)
    if existing_userpageviews.exists():
        # Already have a relevance score for this page for a specific session, so it has been clicked in the last 2 years from this session_key
        existing_userpageviews_count = existing_userpageviews.count()
        user_page = existing_userpageviews.first()
        #user_page = UserPageview.objects.get(session=session, wpid=wpid)
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
        UserPageview.objects.create(user_model=usermodel, session=session, wpid=wpid, aged_score=1)

    return response

from django.shortcuts import redirect

def link(request, id):
    temp_message=""
    # Read data about the link that brought the user to the site.
    if not Redirect.objects.filter(redirect_code=id).exists():
        # The redirect code does not exist in the database. Push user to the shop page instead.
        target_url = 'https://dundlabumi.lv/index.php/veikals/'
        response = redirect(target_url)
    else:
        # A valid redirect code was received.
        redirect_record = Redirect.objects.get(redirect_code=id)
        redirect_usermodel = redirect_record.usermodel
        target_url = redirect_record.target_url
        wpid_of_linked_page = redirect_record.wpid_id

        # Get the session from the received request
        if 's_key' in request.session:
            # A session key is stored in s_key.
            session_key = request.session['s_key']
            temp_message += "s_key present in request.session. "
            # Change the session key to the store value from the cookie.
            #request.session.session_key = session_key
            #request.session.save()
        if not 's_key' in request.session or session_key == None:
            temp_message += "s_key missing or None. "
            request.session.create()
            request.session.save()
            session_key = request.session.session_key
            # Save the session to s_key
            request.session['s_key'] = session_key
            request.session.save()
        if session_key == None:
            temp_message += "s_key still None. "
        if Session.objects.filter(session_key=session_key).exists():
            session = Session.objects.get(session_key=session_key)
        else:
            session = Session.objects.create(session_key=session_key)

        # Get the usermodel for this session. Create if it is not associated.
        # First get a queryset of the usermodels that have this session_key
        usermodels_for_session = session.usermodels.all()
        if len(usermodels_for_session) > 0:
            # A usermodel instance was found for the current session key.
            usermodel = UserModel.objects.get(sessions=session)
            #saved_username = usermodel.username
            #saved_email = usermodel.email
            temp_message += " retrieved usermodel. "
        elif redirect_usermodel is not None :
            # Session is new, but is apparently for an existing username.
            usermodel = redirect_usermodel
            usermodel.sessions.add(session)
            usermodel.save()
            temp_message += " New session, but username known. "
        else:
            # No usermodel exists for this session key. Create one and add the current session.
            usermodel = UserModel.objects.create()
            usermodel.sessions.add(session)
            usermodel.save()
            temp_message += " created usermodel "
            #saved_username = ""
            #saved_email = ""

        # Check for a logged in user.
        session_data = session.get_decoded()
        uid = session_data.get('_auth_user_id')
        if uid is not None:
            user = User.objects.get(id=uid)
            username = user.username
            temp_message += " username = " + str(username)
            user_email = user.email
            temp_message += " user_email = " + str(user_email)
        else:
            # User not logged in.
            username = ""

        # If a username is known, check it is recorded in UserModel.
        if uid is not None:
            # A user is logged in.
            #if usermodel is not None:
            # the redirect link referred to a specific user.
            if usermodel.username is None or usermodel.username == "" or usermodel.username == "saknesar_stats_dev":
                # The username of the specific user is not yet stored in the database.
                usermodel.username=username
                usermodel.save()
                temp_message += " Added username to UserModel"
            #else:
                # User logged in, but the redirect link did not refer to a specific user.
                # See if a user already exists for this email.
            #    if user_email is not None:
            #        if UserModel.objects.filter(email=user_email).exists():
            #            usermodel = UserModel.objects.get(email=user_email)
            #            if usermodel.username is None:
            #                # The username of the specific user is not yet stored in the database.
            #                usermodel.username = username
            #                usermodel.save()
            #                temp_message += " Setting username to UserModel when redirect had no email."
            #        else:
            #            # User is logged in, but is not a subscriber. Create a UserModel for this user.
            #            usermodel = UserModel.objects.create(email=user_email, username=username, session=session)
            #            temp_message += " Created new user for a new logged in user that is not a subscriber."

        #temp_message += " usermodel = " + str(usermodel)
        # Connect the current session to this usermodel, if not already added.

        if usermodel.sessions != session:
            usermodel.sessions.add(session)
            usermodel.save()
            temp_message += " Session linked to user."

        # Create the response to return to the user.
        response = redirect(target_url)
        #if session_key is not None:
        #    response.set_cookie('s_key', session_key)
        #    temp_message += "Setting cookie. "
        #Click.objects.create(redirect_code_id=id, session=session, temp_message = temp_message)
        Click.objects.create(redirect_code=redirect_record, session=session, temp_message=temp_message)

        # Now increment the User / Link relevance score.
        clicked_wpid = WPID.objects.get(wp_id=wpid_of_linked_page)
        if UserLink.objects.filter(session=session, wpid=clicked_wpid).exists():
            # Already have a relevance score for this link for a specific session, so it has been clicked in the last 2 years from this session_key
            user_link = UserLink.objects.get(session=session, wpid=clicked_wpid)
            # Increment aged score by 1 as new link click today.
            user_link.aged_score += 1
            if user_link.user_model is None:
                # Session known, no username associated with the session, but we know the user.
                user_link.user_model = usermodel
            user_link.save()
        else:
            # No relevance score for a usermodel or this session_key so link not clicked in last 2 years.
            UserLink.objects.create(user_model=usermodel, session=session, wpid=clicked_wpid, aged_score=1)

    return redirect(target_url, response=response)

from django.shortcuts import render
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
        reader_usermodel = email.usermodel
        if reader not in readers.keys():
            readers[reader]={}
            user_instance = UserModel.objects.get(email=reader)
            readers[reader]['UserModel_instance'] = user_instance
            readers[reader]['UserModel_id'] = user_instance.id
            sessions_list = user_instance.sessions.values_list('session_key', flat=True)
            # Retrieve the values of the sessions
            sessions_values = Session.objects.filter(session_key__in=sessions_list).values_list('session_key', flat=True)
            readers[reader]['session_list'] = sessions_values
            #reader_usermodels[reader_usermodel] = sessions_values
        reader_clicks = Click.objects.filter(session__in=sessions_values)
        readers[reader]['clicks'] = reader_clicks
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
