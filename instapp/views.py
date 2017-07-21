from django.shortcuts import render, redirect
from forms import SignUpForm, LoginForm, PostForm, LikeForm, CommentForm
from models import User, SessionToken, PostModel, LikeModel, CommentModel
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta
from django.utils import timezone
from instaclone.settings import BASE_DIR
from django.forms.models import model_to_dict
from imgurpython import ImgurClient
import sendgrid
import smtplib
import os
from sendgrid.helpers.mail import *
from django.core.mail import EmailMessage
from django.http import HttpRequest,HttpResponse
from django.http import JsonResponse
from json import dumps
from django.core import serializers

from clarifai.rest import ClarifaiApp
API_KEY="b8500b2bf3104a7b9a228793e2f97668 "


app = ClarifaiApp(api_key=API_KEY)
model = app.models.get('food-items-v1.0')


response = model.predict_by_url(url='https://www.elementstark.com/woocommerce-extension-demos/wp-content/uploads/sites/2/2016/12/pizza.jpg')
print response
email=User.email

sub="Thanks for like or comment on post"
from_email="tanviranga.100@gmail.com"
from_name="Tanvi Ranga"
message="Hello User! You have recently liked or posted a comment on a post.Thanks for using Instaclone."

my_client = sendgrid.SendGridAPIClient(apikey=os.environ.get('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'))
#Function to create payload

def create_payload(sub,message,email):
    from_email = "Your _email_here"
    from_name = "Upload to win"

    payload = {
            "personalizations":[{
                "to":[{"email":email }],
                "subject": sub
            }],
            "from": {
                "email": from_email,
                "name": from_name
            },
            "content": [{
                "type":"text/html",
                "value": message
            }]
        }
    return payload



# Create your views here.
YOUR_CLIENT_ID="6c5b3d0137c9823"
YOUR_CLIENT_SECRET="45cfe34d37335be9695957581aa2d4455beeac7e"
def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # saving data to DB
            user = User(name=name, password=make_password(password), email=email, username=username)
            user.save()
            return render(request, 'success.html')
            # return redirect('login/')
    else:
        form = SignUpForm()

    return render(request, 'index.html', {'form': form})


def login_view(request):
    response_data = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = User.objects.filter(username=username).first()

            if user:
                if check_password(password, user.password):
                    token = SessionToken(user=user)
                    token.create_token()
                    token.save()
                    response = redirect('feed/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                else:
                    response_data['message'] = 'Incorrect Password! Please try again!'

    elif request.method == 'GET':
        form = LoginForm()

    response_data['form'] = form
    return render(request, 'login.html', response_data)


def post_view(request):
    user = check_validation(request)

    if user:
        if request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.cleaned_data.get('image')
                caption = form.cleaned_data.get('caption')
                post = PostModel(user=user, image=image, caption=caption)
                post.save()
                #import pdb;pdb.set_trace()

                path=str(BASE_DIR+"/"+post.image.url)

                client = ImgurClient(YOUR_CLIENT_ID, YOUR_CLIENT_SECRET)

                temp=client.upload_from_path(path,anon=True)
                post.image_url = temp['link']
                post.save()

                return redirect('/feed/')

        else:
            form = PostForm()
        return render(request, 'post.html', {'form' : form})
    else:
        return redirect('/login/')


def feed_view(request):
    user = check_validation(request)
    if user:

        posts = PostModel.objects.all().order_by('-created_on')

        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True

        return render(request, 'feed.html', {'posts': posts})
    else:

        return redirect('/login/')


def like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            LikeModel.objects.create(post_id=post_id, user=user)
            if not existing_like:

                LikeModel.objects.create(post_id=post_id, user=user)




            else:
             existing_like.delete()

            return redirect('/feed/')

    else:
        return redirect('/login/')


def comment_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()
            payload = create_payload(sub, message, email)
            response = my_client.client.mail.send.post(request_body=payload)
            print response


            return redirect('/feed/')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')



# For validating the session
def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            time_to_live = session.created_on + timedelta(days=1)
            if time_to_live > timezone.now():
                return session.user
    else:
        return None