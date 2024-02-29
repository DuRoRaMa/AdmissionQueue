# -*- coding: utf-8 -*-
from django.shortcuts import redirect, render
from django.contrib import auth, messages
from django.views import View
from django.contrib.auth.forms import AuthenticationForm
 
class LoginView(View):
    def get(self, request):
        if auth.get_user(request).is_authenticated:
            return redirect('/')
        else:
            form = AuthenticationForm()
            return render(request, 'Login.html', {'login_form': form})
 
    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                next = request.GET.get('next') # получаем предыдущий url
                if next == '/admin/login/' and request.user.is_staff:
                    return redirect('/admin/')
                if next is not None:
                    return redirect(next)
                else:
                    return redirect('queue:RegTalon')
            else:
                messages.error(request,"Invalid username or password")
            
        return render(request, 'Login.html', {'login_form': form})
 
class LogoutView(View):
    def get(self, request):
        auth.logout(request)
        messages.info(request, "You have successfully logged out.") 
        return redirect("accounts:login")