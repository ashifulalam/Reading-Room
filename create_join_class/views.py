import json
import uuid
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CreateClassRoomForm, ReadingMaterialForm
from .models import *


# This method is used to create class. It creates a class with the POST data retrieved from the user via form
# and also generates a unique class code for other users to join.
@login_required
def create_class(request):
    if request.method == "GET":
        return render(request, 'create_join_class/create_class.html', {'form': CreateClassRoomForm})
    else:
        try:
            form_data = CreateClassRoomForm(request.POST)
            new_class = form_data.save(commit=False)
            new_class.teacher = request.user
            new_class.classCode = uuid.uuid4().hex[:6].upper()
            new_class.save()
            return redirect('home_classroom')
        except ValueError:
            return render(request, 'create_join_class/create_class.html',
                          {'form': CreateClassRoomForm, 'error': 'Bad data passed in. Try again!'})

# This method is used for logging in. It redirects the user to homepage if credentials match.
# Else it prompts the user to reenter credentials.
def index(request):
    if request.method == 'GET':
        return render(request, 'create_join_class/index.html', {'form': AuthenticationForm()})
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'create_join_class/index.html',
                          {'form': AuthenticationForm(), 'error': 'Username or password is incorrect'})
        else:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home_classroom')


create_join_class/models.py
# This class is for all classrooms that are going to be created. Each classroom has a name, section, code,
# one teacher and zero to many students.
class ClassRoom(models.Model):
    name = models.CharField(max_length=100)
    section = models.IntegerField()
    classCode = models.CharField(max_length=6, null=True, blank=True, unique=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_of_the_class')
    students = models.ManyToManyField(User, blank=True, related_name='student_of_the_class')

    def __str__(self):
        return self.name + '.' + str(self.section) + ' ID:' + str(self.id)


# This method is the homepage where the user can see his/her created and joined classes.
# It returns the homepage.
@login_required
def home_classroom(request):
    created_classes = ClassRoom.objects.filter(teacher=request.user)
    joined_classes = ClassRoom.objects.filter(students__in=[request.user.id])
    return render(request, 'create_join_class/home_classroom.html',
                  {'user': request.user, 'created_classes': created_classes, 'joined_classes': joined_classes})


