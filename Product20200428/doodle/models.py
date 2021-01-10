from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    job = models.IntegerField()
    worker = models.IntegerField()
    data = models.TextField()
    is_save = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
