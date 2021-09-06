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


# This method is used to delete any reading material uploaded by the teacher of the class. The teacher
# can only delete pdf files.
@login_required
def deleteReadingMaterial(request, classroom_pk, readingMaterial_pk):
    if request.method == "POST":
        readingmaterial = ReadingMaterial.objects.get(pk=readingMaterial_pk)
        readingmaterial.delete()
        return redirect('viewCreatedReadingMaterial', classroom_pk)


# This method is used to view the created reading materials by the teacher.
# It shows all the reading materials created by the teacher for a particular class.
@login_required 
def viewCreatedReadingMaterial(request, created_pk):
    materialTeacher = ReadingMaterial.objects.filter(classroom_id=created_pk, uploader=request.user)
    return render(request, "create_join_class/viewCreatedReadingMaterial.html", {'materialTeacher': materialTeacher})

# This method is used to view the reading materials as a student.
# It shows all the reading materials uploaded by the teacher for a particular class.
@login_required 
def viewJoinedReadingMaterial(request, joined_pk):
    materialStudent = ReadingMaterial.objects.filter(classroom_id=joined_pk, classroom__students__in=[request.user.id])
    return render(request, "create_join_class/viewJoinedReadingMaterial.html", {'materialStudent': materialStudent})

# This method is used to show pdf files to the students and returns and a html page where the pdf file is
# embedded.

@login_required
def viewPDF(request, filename, material_id):
    return render(request, "create_join_class/viewPDF.html", {'filename': filename, 'material_id': material_id,'username': request.user.username})
# This method is for any user to create an account first before doing anything else.
# It redirects the user to homepage if account is created successfully. Else it prompts the
# user to re-enter his credentials.
def signup_user(request):
    if request.method == "GET":
        return render(request, 'create_join_class/signupuser.html', {'form': UserCreationForm()})
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('home_classroom')
            except IntegrityError:
                return render(request, 'create_join_class/signupuser.html',
                              {'form': UserCreationForm(), 'error': 'Username is '
                                                                    'already taken!'})
        else:
            return render(request, 'create_join_class/signupuser.html',
                          {'form': UserCreationForm(), 'error': 'Password did not '
                                                                'match!'})

# This method logs out the user from the site and redirects him/her to the login page.
@login_required
def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return redirect('index')



                          


                          
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




# This method is used to join class. It checks if the user has uploaded an image of himself and only then
# allows the user to enter the classroom code. If the code matches the user successfully jons the class. Else,
# the system prompts the user to reenter code.
@login_required
def join_class(request):
    if request.method == "GET":

            return render(request, 'create_join_class/join_class.html')

    else:
        # checking if the class code that user entered does exist or not
        try:
            classobj = ClassRoom.objects.get(classCode=request.POST['classCode'])
        except ClassRoom.DoesNotExist:
            return render(request, 'create_join_class/join_class.html',
                          {'error': 'No class found with that class code!'})

        if classobj.teacher == request.user:
            return render(request, 'create_join_class/join_class.html', {'error': 'You are the teacher of this class!'})
        else:
            user = request.user
            classobj.students.add(user)
            return redirect('home_classroom')


# This method is used to show the created classrooms by a user.
# It returns a html page with links to all created classrooms.
@login_required
def viewcreatedclassroom(request, classroom_pk):
    classroom = get_object_or_404(ClassRoom, teacher=request.user, pk=classroom_pk)
    return render(request, "create_join_class/viewcreatedclassroom.html", {'classroom': classroom})


# This method is used to show the joined classrooms by a user.
# It returns a html page with links to all joined classrooms.
@login_required
def viewjoinedclassroom(request, classroom_pk):
    classroom = get_object_or_404(ClassRoom, students__in=[request.user.id], pk=classroom_pk)
    return render(request, "create_join_class/viewjoinedclassroom.html", {'classroom': classroom})
