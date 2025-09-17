# models.py
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
import shortuuid
from django.contrib.auth.models import User
import os
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField
import re

class ChatGroup(models.Model):
    group_name = models.CharField(max_length=128, unique=True, blank=True)
    groupchat_name = models.CharField(max_length=128, null=True, blank=True)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="groupchats", blank=True, null=True, on_delete=models.SET_NULL)    
    users_online = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='online_in_groups', blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_groups', blank=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.group_name
    
    def save(self, *args, **kwargs):
        if not self.group_name:
            self.group_name = shortuuid.uuid()
        super().save(*args, **kwargs)

class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, related_name='chat_messages', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.CharField(max_length=300, blank=True, null=True)
    file = CloudinaryField('file', folder='chat_files/', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    delivered_to = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='delivered_messages', blank=True)
    seen_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='seen_messages', blank=True)

    @property
    def filename(self):
        if self.file:
            # For Cloudinary, use public_id instead of name
            return self.file.public_id.split('/')[-1]
        return None
    
    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None

    def __str__(self):
        if self.body:
            return f'{self.author.username} : {self.body}'
        elif self.file:
            return f'{self.author.username} : {self.filename}'
        
    def clean(self):
        if not self.body and not self.file:
            raise ValidationError("Message must have either body text or a file.")
    
    def save(self, *args, **kwargs):
        if not self.body and not self.file:
            return
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created']

    @property
    def is_image(self):
        if not self.file:
            return False
            
        # Get the file extension from the URL
        url = str(self.file)
        
        # Extract file extension from URL
        match = re.search(r'\.([a-zA-Z0-9]+)(?:\?|$)', url)
        if match:
            extension = match.group(1).lower()
        else:
            return False
            
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'tiff']
        return extension in image_extensions

    @property
    def is_gif(self):
        if not self.file:
            return False
            
        url = str(self.file)
        match = re.search(r'\.([a-zA-Z0-9]+)(?:\?|$)', url)
        if match:
            extension = match.group(1).lower()
            return extension == 'gif'
        return False

    @property
    def is_pdf(self):
        if not self.file:
            return False
            
        url = str(self.file)
        match = re.search(r'\.([a-zA-Z0-9]+)(?:\?|$)', url)
        if match:
            extension = match.group(1).lower()
            return extension == 'pdf'
        return False

    @property
    def file_type(self):
        """Return the file type for better handling in templates"""
        if not self.file:
            return None
            
        url = str(self.file)
        match = re.search(r'\.([a-zA-Z0-9]+)(?:\?|$)', url)
        if match:
            extension = match.group(1).lower()
            
            if extension in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff']:
                return 'image'
            elif extension == 'gif':
                return 'gif'
            elif extension == 'pdf':
                return 'pdf'
            elif extension in ['doc', 'docx', 'txt', 'rtf']:
                return 'document'
            elif extension in ['mp4', 'mov', 'avi', 'wmv']:
                return 'video'
            elif extension in ['mp3', 'wav', 'ogg']:
                return 'audio'
            else:
                return 'file'
        return 'file'