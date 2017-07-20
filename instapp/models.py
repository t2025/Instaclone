# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import uuid
class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    #phone = models.CharField(max_length=30)
    age = models.IntegerField(default=0)
    username = models.CharField(max_length=120)
    password = models.CharField(max_length=40)
    has_verified_mobile = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)


class SessionToken(models.Model):
    user = models.ForeignKey(User)
    session_token = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)

    def create_token(self):
        self.session_token = uuid.uuid4()



class PostModel(models.Model):
  user = models.ForeignKey(User)
  image = models.FileField(upload_to='user_images')
  image_url = models.CharField(max_length=255)
  caption = models.CharField(max_length=240)
  created_on = models.DateTimeField(auto_now_add=True)
  updated_on = models.DateTimeField(auto_now=True)
  has_liked = False



  @property
  def like_count(self):
      return len(LikeModel.objects.filter(post=self))

  @property
  def comments(self):
      return CommentModel.objects.filter(post=self).order_by('-created_on')


class LikeModel(models.Model):
    user = models.ForeignKey(User)
    post = models.ForeignKey(PostModel)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

class CommentModel(models.Model):
  user = models.ForeignKey(User)
  post = models.ForeignKey(PostModel)
  comment_text = models.CharField(max_length=555)
  created_on = models.DateTimeField(auto_now_add=True)
  updated_on = models.DateTimeField(auto_now=True)