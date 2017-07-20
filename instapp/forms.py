from django import forms
from models import User
from models import PostModel,LikeModel,CommentModel
class SignUpForm(forms.ModelForm):
  class Meta:
    model = User
    fields=['email','username','name','password']

class LoginForm(forms.ModelForm):
      class Meta:
          model = User
          fields = ['username', 'password']

class PostForm(forms.ModelForm) :
    caption = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Caption'}))


    class Meta:
        model=PostModel
        fields=['image','caption']



class LikeForm(forms.ModelForm):
    class Meta:
        model = LikeModel
        fields = ['post']


class CommentForm(forms.ModelForm):

    class Meta:
        model = CommentModel
        fields = ['comment_text', 'post']