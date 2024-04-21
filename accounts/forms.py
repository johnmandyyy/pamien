from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import PersonAccount, ShopifyAccess

ID_CHOICES = (
    ('Driver License', 'Driver License'),
    ('Postal ID', 'Postal ID'),
)

ACCOUNT_TYPE_CHOICES = (
    ('Buyer', 'Buyer'),
    ('Seller', 'Seller'),
)

class RegistrationForm(UserCreationForm):
    username = forms.EmailField(max_length=254, required=True, help_text='Required. Enter a valid email address.',widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address', 'class': 'input-box'}))
    first_name = forms.CharField(max_length=256, required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter your first name', 'class': 'input-box'}))
    last_name = forms.CharField(max_length=256, required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter your last name', 'class': 'input-box'}))
    phone = forms.IntegerField(required=True, widget=forms.TextInput(attrs={'type':'number','min':'09000000000','max':'99999999999','placeholder': 'Enter your phone number', 'class': 'input-box'}))
    address = forms.CharField(max_length=256, required=True, widget=forms.Textarea(attrs={'placeholder': 'Enter your address', 'class': 'input-box'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder': 'Password','class': 'input-box'}))
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password','class': 'input-box'}))
    id_options = forms.ChoiceField(choices=ID_CHOICES, required=True)
    id_image = forms.ImageField(required=True)
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPE_CHOICES, required=True)
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 'phone', 'address', 'id_options', 'id_image', 'account_type')

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        if commit:
            user.save()
            person_account = user
            person_account.first_name = self.cleaned_data.get('first_name')
            person_account.last_name = self.cleaned_data.get('last_name')
            person_account.phone = self.cleaned_data.get('phone')
            person_account.address = self.cleaned_data.get('address')
            person_account.id_options = self.cleaned_data.get('id_options')
            person_account.id_image = self.cleaned_data.get('id_image')
            person_account.account_type = self.cleaned_data.get('account_type')
            person_account.save()
        return user
    
class LoginForm(forms.Form):
    username = forms.EmailField(max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)

class ShopifyForm(forms.ModelForm):
    class Meta:
        model = ShopifyAccess
        fields = ['user', 'shopify_url', 'api_key', 'api_secret', 'access_token']
        widgets = {
            'user': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.initial['user'] = user
