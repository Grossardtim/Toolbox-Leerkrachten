import re
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

COLORS = {
    'menu': ('Menukolom', '#ffffff'), 'workspace': ('Werkvlak', '#f7f8fc'),
    'tools': ('Rechterkolom', '#f3d8ed'), 'module': ('Modulehoofding', '#85175e'),
    'section': ('Sectiehoofding', '#d4e3ff'), 'goal': ('Doelhoofding', '#ecb9e7'),
    'accent': ('Knoppen en accenten', '#bf0046'),
}

def foreground(hex_color):
    rgb = [int(hex_color[i:i+2], 16)/255 for i in (1, 3, 5)]
    lum = sum(v*w for v,w in zip([v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb], [.2126,.7152,.0722]))
    return '#111111' if lum > .179 else '#ffffff'

def theme_css(user):
    saved = user.ui_colors if user.is_authenticated and isinstance(user.ui_colors, dict) else {}
    colors = {key: saved.get(key, default) for key, (_, default) in COLORS.items()}
    colors = {key: value if re.fullmatch(r'#[0-9a-fA-F]{6}', str(value)) else COLORS[key][1] for key,value in colors.items()}
    return ';'.join(f'--ui-{key}:{value};--ui-{key}-text:{foreground(value)}' for key,value in colors.items())

class PreferencesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key,(label,default) in COLORS.items():
            self.fields[key] = forms.RegexField(regex=r'^#[0-9a-fA-F]{6}$', label=label,
                initial=default, widget=forms.TextInput(attrs={'type': 'color'}))

@login_required
def preferences(request):
    form = PreferencesForm(request.POST or None, initial=request.user.ui_colors)
    if request.method == 'POST':
        if request.POST.get('action') == 'reset':
            request.user.ui_colors = {}
        elif form.is_valid():
            request.user.ui_colors = form.cleaned_data
        else:
            return render(request, 'accounts/preferences.html', {'form': form, 'nav': 'preferences'})
        request.user.save(update_fields=['ui_colors'])
        from evaluations.views import log
        log(request.user, 'kleurvoorkeuren opgeslagen', request.user)
        messages.success(request, 'Je persoonlijke kleuren zijn opgeslagen.')
        return redirect('preferences')
    return render(request, 'accounts/preferences.html', {'form': form, 'nav': 'preferences'})
