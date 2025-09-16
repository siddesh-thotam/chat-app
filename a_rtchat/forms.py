from django.forms import ModelForm
from django import forms
from .models import *

class ChatmessageCreateForm(ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['body', 'file']  # Include file field
        widgets = {
            'body': forms.TextInput(attrs={
                'placeholder': 'Add message...', 
                'class': 'p-4 text-black', 
                'maxlength': '300', 
                'autofocus': True
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        body = cleaned_data.get('body', '').strip()
        file = cleaned_data.get('file')
        
        if not body and not file:
            raise ValidationError("Message must have either text or a file.")
        
        return cleaned_data
    
class NewGroupForm(ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['groupchat_name']
        widgets = {
                'groupchat_name' : forms.TextInput(attrs={
                    'placeholder':'Add Name.....',
                    'class':'p-4 text-black',
                    'max_length':'300',
                    'autofocus':True
                })
        }

class ChatRoomEditForm(ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['groupchat_name']
        widgets = {
            'groupchat_name' : forms.TextInput(attrs={
                'class': 'p-4 text-xl font-bold mb-4',
                'max_Length':'300',
            }),
        }