from django.shortcuts import render
from .forms import LoginForm
from django.contrib.auth.views import LoginView
from django.views import generic

class TopView(generic.TemplateView):
    template_name = 'top.html'

class Login(LoginView):
    form_class = LoginForm
    template_name = 'login.html'