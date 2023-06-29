from django.utils.translation import gettext as _
from django import forms
from users.models import User
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import re

class AccountForm(forms.ModelForm):
    # パスワード入力：非表示対応
    password = forms.CharField(widget=forms.PasswordInput(),label="Password")

    class Meta():
        model = User
        fields = ('email', 'password', 'username')
        labels = {'email':'Email', 'username':'UserName'}

    def clean(self):
        cleaned_data = super().clean()
        if "email" not in cleaned_data:
            raise forms.ValidationError(_('Error : Email Not Found'), code="empty")
        if "password" not in cleaned_data:
            raise forms.ValidationError(_('Error : Password Not Found'), code="empty")
        else:
            check = cleaned_data["password"]
            if len(check) < 8:
                raise forms.ValidationError(_('Error : Password must be at least 8 characters, including upper and lower case letters and numbers.'), code="password")
            result1 = re.search("[a-z]+", check)
            if not result1:
                raise forms.ValidationError(_('Error : Lowercase letters not found in password.'), code="lowercase")
            result2 = re.search("[A-Z]+", check)
            if not result2:
                raise forms.ValidationError(_('Error : Uppercase letters not found in password.'), code="uppercase")
            result3 = re.search("[0-9]+", check)
            if not result3:
                raise forms.ValidationError(_('Error : No digits found in password.'), code="figure")

class ChatForm(forms.Form):
    target_type = forms.fields.ChoiceField(
        choices = (("1", '日本語'), ("2", '英語'), ("3", 'エスペラント語')),
        label='target_type',
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 150px'})
    )

    sentence = forms.CharField(required=True)

    def clean(self):
        cleaned_data = super().clean()
        target_type = cleaned_data["target_type"]
        try:
            sentence = cleaned_data["sentence"]
#            if len(sentence) == 1:
#                raise forms.ValidationError(_('ttttt'), code="empty")                
        except Exception as e:
            raise forms.ValidationError(_('Error : Sentence Not Found'), code="empty")

class SummarizeForm(forms.Form):
    target_type = forms.fields.ChoiceField(
        choices = (("1", '短く要約'), ("2", 'すごく短く要約'), ("3", '子供向けに要約')),
        label='target_type',
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 200px'})
    )

    sentence = forms.CharField(widget=forms.Textarea(attrs={'cols': '100', 'rows': '12'}))

    def clean(self):
        cleaned_data = super().clean()
        target_type = cleaned_data["target_type"]
        try:
            sentence = cleaned_data["sentence"]
#            if len(sentence) == 1:
#                raise forms.ValidationError(_('ttttt'), code="empty")                
        except Exception as e:
            raise forms.ValidationError(_('Error : Sentence Not Found'), code="empty")

