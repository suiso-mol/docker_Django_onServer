import uuid
from django.db import models

class Server(models.Model):
    sv_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    ip = models.GenericIPAddressField(protocol='both')
    os = models.CharField(max_length=100)
    usage = models.CharField(blank=True, max_length=200)
    remark = models.CharField(blank=True, max_length=200)
    deleted = models.BooleanField(default=False)
    update_date = models.DateTimeField(auto_now=True)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return self.name

class Package(models.Model):
    pkg_name = models.CharField(primary_key=True, max_length=100)
    architecture = models.CharField(blank=True, max_length=50)
    description = models.CharField(blank=True, max_length=100)
    remark = models.CharField(blank=True, max_length=200)
    deleted = models.BooleanField(default=False)
    update_date = models.DateTimeField(auto_now=True)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return self.pkg_name

class Content(models.Model):
    sv_id = models.ForeignKey(Server, on_delete=models.CASCADE)
    pkg_name = models.ForeignKey(Package, on_delete=models.CASCADE)
    sv_pkg = models.SlugField(primary_key=True, blank=False,unique=True,max_length=150)
    version = models.CharField(max_length=50)
    deleted = models.BooleanField(default=False)
    update_date = models.DateTimeField(auto_now=True)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return self.sv_pkg
    
