from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
from .models import User

class FirstAdminForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']

class UserChoiceAuthenticationForm(AuthenticationForm):
    username = forms.ChoiceField(label='Gebruiker', choices=[], widget=forms.Select(attrs={'autofocus': True}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].choices = [('', 'Kies je account')] + [
            (u.username, f'{u.get_full_name()} ({u.username})' if u.get_full_name() else u.username)
            for u in User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')]

class TeacherForm(forms.ModelForm):
    password1 = forms.CharField(label='Nieuw wachtwoord', required=False, widget=forms.PasswordInput,
        help_text='Minstens 12 tekens. Bij wijzigen leeg laten om het huidige wachtwoord te behouden.')
    password2 = forms.CharField(label='Herhaal nieuw wachtwoord', required=False, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'can_evaluate', 'can_export', 'view_all_teachers', 'visible_teachers']
        labels = {'username':'Gebruikersnaam', 'first_name':'Voornaam', 'last_name':'Achternaam',
                  'email':'E-mailadres', 'is_active':'Account actief',
                  'can_evaluate':'Evaluaties', 'can_export':'Excel-export van zichtbare evaluaties', 'view_all_teachers':'Lessen van alle leerkrachten bekijken', 'visible_teachers':'Lessen van deze leerkrachten bekijken'}
        help_texts = {'username':'Unieke naam voor dit account.', 'can_export':'Vereist ook toegang tot Evaluaties.'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['visible_teachers'].queryset = User.objects.filter(is_superuser=False).exclude(pk=self.instance.pk)
        self.fields['visible_teachers'].help_text = 'Alleen van toepassing wanneer alle lessen bekijken uit staat. Lesresultaten zijn bewerkbaar door maker en admin. Tool-administratie blijft voor iedereen gedeeld.'

    def clean(self):
        data = super().clean()
        password = data.get('password1')
        if not self.instance.pk and not password:
            self.add_error('password1', 'Stel een wachtwoord in voor het nieuwe account.')
        if password != data.get('password2'):
            self.add_error('password2', 'De wachtwoorden zijn niet gelijk.')
        if password:
            candidate = User(username=data.get('username',''), first_name=data.get('first_name',''),
                last_name=data.get('last_name',''), email=data.get('email',''))
            try:
                validate_password(password, candidate)
            except forms.ValidationError as error:
                self.add_error('password1', error)
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            self.save_m2m()
        return user
