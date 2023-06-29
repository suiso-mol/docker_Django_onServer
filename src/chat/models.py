from django.db import models

# Create your models here.
class Chatlog(models.Model):
    log_id = models.AutoField(primary_key=True, editable=False)
    user = models.CharField(max_length=100)
    relation_id = models.IntegerField(default=0)
    input_text = models.TextField()
    output_text = models.TextField()
    check = models.BooleanField(default=True)
    update_date = models.DateTimeField(auto_now=True)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return self.input_text