from django.shortcuts import render, redirect
from django.shortcuts import HttpResponseRedirect
from django.core.urlresolvers import reverse
from forms import SignUpForm, LoginForm, PostForm, LikeForm, CommentForm
from models import User, SessionToken, PostModel, LikeModel, CommentModel
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta
from django.utils import timezone
from instaclone.settings import BASE_DIR
#importing ImGur
from imgurpython import ImgurClient
#importing sendgrid for sending emails
import sendgrid
from sendgrid.helpers.mail import *
#imporing Clarifai
from clarifai.rest import ClarifaiApp ,Image
import json
import requests
API_KEY="b8500b2bf3104a7b9a228793e2f97668 "

#Clarifai code demo


email=User.email


#Sendgrid Api call
SENDGRID_APIKEY = "YOUR_API_KEY-HERE"
sg = sendgrid.SendGridAPIClient(apikey=SENDGRID_APIKEY)
#IMGUR client Id and secret
YOUR_CLIENT_ID="6c5b3d0137c9823"
YOUR_CLIENT_SECRET="45cfe34d37335be9695957581aa2d4455beeac7e"
#Method for signup
def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        #Form validation check
        if form.is_valid():
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # saving data to DB
            user = User(name=name, password=make_password(password), email=email, username=username)
            if (len(username)>=5 and len(password)>=4):
             user.save()
             return render(request, 'success.html')



    else:
        form = SignUpForm()

    return render(request, 'index.html', {'form': form})

#Login view method
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

#Method for posting pictures
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
                # logos for awarding points

                url = post.image_url
                app = ClarifaiApp(api_key=API_KEY)
                model = app.models.get('logo')
                image = Image(url=url)
                response = model.predict([image])
                data = response['outputs'][0]['data']['regions'][0]['data']['concepts'][0]['name']
                print data
                if data=="Starbucks":
                   userpoints=user.points+20
                   print userpoints

                   user.points=userpoints
                   user.save()
                   print user
                elif data=="Apple Inc":
                    userpoints=user.points+50
                    print userpoints
                    user.points=userpoints
                    user.save()
                elif data=="Dove":
                    userpoints = user.points + 70
                    print userpoints
                    user.points = userpoints
                    user.save()
                elif data=="Burger King":
                    userpoints=user.points+150
                    print userpoints
                    user.points=userpoints
                    print userpoints
                    user.save()




                return redirect('/feed/')

        else:

          form = PostForm()
        return render(request, 'post.html', {'form': form})
    else:
     return redirect('/login/')
#points view to see awarded points
def points_view(request):
    user=check_validation(request)
    if user:
     points=user.points
     print points
     return render(request, 'points.html',{'points':points})

def feed_view(request):
    user = check_validation(request)
    if user:
        username=user.username

        posts = PostModel.objects.all().order_by('-created_on')

        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True

        return render(request, 'feed.html', {'posts': posts})
        #for query string
        if posts:
            return HttpResponseRedirect(reverse('/feed/') +"?filter=username&sort=newest")
    else:

        return redirect('/login/')

 #Method for liking a picture
def like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            if not existing_like:
                LikeModel.objects.create(post_id=post_id, user=user)
                #code for sending an email after successful like
                from_email = Email("test@sendgrid.com")
                to_email = Email("tanviranga.100@gmail.com")
                subject = "Welcome to Instaclone"
                content = Content("text/plain", "Thanks for liking this post!")
                mail = Mail(from_email, subject, to_email, content)
                response = sg.client.mail.send.post(request_body=mail.get())
                print(response.status_code)
                print(response.body)
                print(response.headers)

            else:
                existing_like.delete()
            return redirect('/feed/')
    else:
        return redirect('/login/')

#code for posting comment on pictures
def comment_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()
            #code for sending email after successful comment
            from_email = Email("test@sendgrid.com")
            to_email = Email("tanviranga.100@gmail.com")
            subject = "Welcome to instaclone"
            content = Content("text/plain", "Thanks for commenting on this post")
            mail = Mail(from_email, subject, to_email, content)
            response = sg.client.mail.send.post(request_body=mail.get())
            print(response.status_code)
            print(response.body)
            print(response.headers)


            return redirect('/feed/')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')


def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            time_to_live = session.created_on + timedelta(days=1)
            if time_to_live > timezone.now():
                return session.user
    else:
        return None




#Logging out
def logout_view(requests):
    response = HttpResponseRedirect('/login/')
    response.delete_cookie('session_token')

    return response




