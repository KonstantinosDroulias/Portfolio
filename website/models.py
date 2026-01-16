from django.db import models

# Create your models here.

class ContactForm(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=100)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "f{self.name} - ({self.email}) - {self.created}"


class MyInfo(models.Model):
    portrait = models.ImageField()
    email = models.EmailField()
    phone = models.CharField(max_length=100)

