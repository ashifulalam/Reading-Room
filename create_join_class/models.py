from django.db import models
from django.contrib.auth.models import User
from .validators import validate_file_extension, validate_image_extension
from private_storage.fields import PrivateFileField
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver


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


# This class is for all the reading materials that any teacher is going to upload. Each reading material object
# has a name, file along with which classroom it belongs to and who uploaded the reading material.
class ReadingMaterial(models.Model):
    name = models.CharField(max_length=100)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='classroom')
    readingFile = PrivateFileField(upload_to='uploads/ReadingMaterial/', validators=[validate_file_extension])
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploader')

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        self.readingFile.delete()  # delete instance path
        super().delete(*args, **kwargs)  # Call the "real" delete() method.


# This class is for the reading info of all the reading materials created. Each reading info object will contain
# a reading material and a corresponding reading info JSON field. The JSON field will hold the name of the student
# reading the material as key and the time spent on the material by the student as the value.
class ReadingInfo(models.Model):
    material_id = models.ForeignKey(ReadingMaterial, on_delete=models.CASCADE)
    material_info = models.JSONField(null=True)

    def __str__(self):
        return str(self.material_id)



