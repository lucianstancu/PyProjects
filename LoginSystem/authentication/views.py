from django.shortcuts import redirect, render
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from loginsystem import settings
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_text
from . tokens import generate_token


# Create your views here.

def home(request):
    return render(request, "authentication/index.html")

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        
        #verifies if the username exists
        if User.objects.filter(username=username):
            messages.error(request, "Username already exists! Try another username")
            return redirect('home')

        #verifies if the email is already registred
        if User.objects.filter(email=email):
            messages.error(request, "Email already registred!")
            return redirect('home')

        #checks the length of the username
        if len(username)>10:
            messages.error(request, "Username too long!")
        
        #checks the confirmation of password
        if pass1 != pass2:
            messages.error(request, "Passwords didn't match!")

        #checks if the username is numbers only
        if not username.isalnum():
            messages.error(request, "Username must contain only numbers")

        # creates user object with username, email, password
        myuser = User.objects.create_user( username, email, pass1)
        myuser.first_name = fname  # assigns first name to user object
        myuser.last_name = lname   # assigns first name to user object
        myuser.is_active = False
        myuser.save()

        messages.success(request, "Your account has been successfully created")

        # Email send to new created account

        subject = "Welcome to Virtutii Residence!"
        message = "Hello" + myuser.first_name + "!\n" + "Thank you for visiting our website\n" + "Please confirm your email address in order to activate your account"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)
        
        # Email address confirmation email

        current_site = get_current_site(request)
        email_subject = "Confirm your email @ Virtutii Residence Login"
        message2 = render_to_string('email_confirmation.html',{

            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser),
        })

        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER
            [myuser.email],
        )
        email.fail_silently = True
        email.send()

        return redirect('signin')

    return render(request, "authentication/signup.html")

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']

        #authentification based on the 2 arguments 
        user = authenticate(username=username, password=pass1)

        if user is not None:
            login(request, user)
            fname = user.first_name
            return render(request, "authentication/index.html", {'fname':fname})

        else:
            messages.error(request, "Bad credentials")
            return redirect('home')
    return render(request, "authentication/signin.html")

def signout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('home')

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None
    
    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        return redirect('home')
    else:
        return render(request, 'activation_failde.html')