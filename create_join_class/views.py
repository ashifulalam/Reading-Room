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


# This method is used to upload reading material by the teacher of the class. The teacher
# can only upload pdf files as reading material. If upload is successful, the teacher
# is redirected to the created classroom html. Else the teacher is prompted to upload the file again.
@login_required
def uploadReadingMaterial(request, classroom_pk): 
    if request.method == 'GET':
        try:
            classroom = ClassRoom.objects.get(teacher=request.user, pk=classroom_pk)
        except ClassRoom.DoesNotExist:
            return render(request, "create_join_class/uploadReadingMaterial.html",
                          {'error': 'You don\'t have upload permissions to this classroom!'})
        form = ReadingMaterialForm()
        return render(request, "create_join_class/uploadReadingMaterial.html", {'form': form})
    else:
        form = ReadingMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            newmaterial = form.save(commit=False)
            newmaterial.classroom = ClassRoom(pk=classroom_pk)
            newmaterial.uploader = User(request.user.id)
            newmaterial.save()
            messages.success(request, 'File Upload Successful')
            return redirect('viewCreatedReadingMaterial', classroom_pk)
        else:
            return render(request, "create_join_class/uploadReadingMaterial.html", {'form': form})

