from django import forms
from .models import Year, Subject, Classroom, Student, Goal, Lesson, StudyDirection

class StudyDirectionForm(forms.ModelForm):
    class Meta:
        model = StudyDirection
        fields = ['name']
        help_texts = {
            'name': 'Bijvoorbeeld: "ASO", "TSO", "BSO", "KSO". Studierichtingen zijn uniek per leerkracht.',
        }

class YearForm(forms.ModelForm):
    class Meta:
        model = Year
        fields = ['name']
        help_texts = {
            'name': 'Bijvoorbeeld: "2024-2025". Schooljaren zijn uniek per leerkracht.',
        }

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'study_directions']
        widgets = {'study_directions': forms.CheckboxSelectMultiple}
        help_texts = {
            'name': 'Bijvoorbeeld: "Wiskunde", "Nederlands", "Biologie".',
            'study_directions': 'Selecteer de studierichtingen waar dit vak toe behoort.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['study_directions'].required = True

    def clean_study_directions(self):
        directions = self.cleaned_data['study_directions']
        if self.instance.pk and self.instance.classroom_set.exclude(study_direction__in=directions).exists():
            raise forms.ValidationError('Dit vak is nog gekoppeld aan een klas van een verwijderde studierichting. Pas eerst de klaskoppeling aan.')
        return directions

class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['name', 'study_direction', 'grade', 'subjects', 'archived']
        widgets = {'subjects': forms.CheckboxSelectMultiple}
        help_texts = {
            'name': 'Bijvoorbeeld: "1A", "2B", "3Wet".',
            'grade': 'Leerjaar (1-7). Bepaalt welke doelen beschikbaar zijn.',
            'subjects': 'Selecteer de vakken die deze klas volgt.',
            'archived': 'Gearchiveerde klassen zijn niet zichtbaar in nieuwe lessen.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['study_direction'].required = True

    def clean(self):
        data = super().clean()
        direction = data.get('study_direction')
        if direction and any(not subject.study_directions.filter(pk=direction.pk).exists() for subject in data.get('subjects', [])):
            self.add_error('subjects', 'Kies alleen vakken die aan deze studierichting gekoppeld zijn.')
        return data

    def save(self, commit=True):
        self.instance.direction = self.cleaned_data['study_direction'].name
        return super().save(commit=commit)

class StudentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["classroom"].label_from_instance = lambda c: f"{c.direction_name} · {c.name} · {c.year.name}"

    class Meta:
        model = Student
        fields = ['classroom', 'name', 'active']
        labels = {'classroom': 'Klas'}
        help_texts = {
            'name': 'Volledige naam van de leerling.',
            'active': 'Inactieve leerlingen verschijnen niet in nieuwe lessen.',
        }

class GoalForm(forms.ModelForm):
    evaluation_points = forms.CharField(label='Subdoelen (optioneel)', required=False, widget=forms.Textarea(attrs={'rows': 7}),
        help_text='Eén subdoel per regel. Laat leeg om de BK zelf te beoordelen. Alle beoordelingspunten tellen even zwaar.')
    class Meta:
        model = Goal
        fields = ['study_direction', 'stage', 'code', 'title', 'archived']
        widgets = {'title': forms.Textarea(attrs={'rows': 2})}
        help_texts = {
            'study_direction': 'Studierichting waar dit doel toe behoort.',
            'stage': 'Graad (1e, 2e of 3e).',
            'code': 'Unieke code voor dit doel (bijv. "LPD-01").',
            'title': 'Omschrijving van het leerplandoel.',
            'archived': 'Gearchiveerde doelen zijn niet zichtbaar in nieuwe lessen.',
        }

    def clean_evaluation_points(self):
        lines = [line.strip() for line in self.cleaned_data['evaluation_points'].splitlines() if line.strip()]
        if any(len(line) > 500 for line in lines):
            raise forms.ValidationError('Elk subdoel mag maximaal 500 tekens bevatten. Verkort de tekst of splits op in meerdere subdoelen.')
        if len(lines) != len(set(lines)):
            raise forms.ValidationError('Geef elk subdoel slechts één keer op.')
        return lines

class LessonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["classroom"].label_from_instance = lambda c: f"{c.direction_name} · {c.name} · {c.year.name}"

    class Meta:
        model = Lesson
        fields = ['classroom', 'subject', 'title', 'date']
        labels = {'classroom': 'Klas', 'subject': 'Vak'}
        widgets = {'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}
        help_texts = {
            'title': 'Onderwerp of thema van de les (max. 180 tekens).',
            'date': 'Datum waarop de les heeft plaatsgevonden.',
        }

    def clean(self):
        data = super().clean()
        classroom, subject = data.get('classroom'), data.get('subject')
        if classroom and subject and not classroom.subjects.filter(pk=subject.pk).exists():
            self.add_error('subject', 'Dit vak is niet gekoppeld aan deze klas. Pas dit aan via Beheer.')
        if classroom and classroom.grade is None:
            self.add_error('classroom', 'Vul eerst het leerjaar van deze klas in via Beheer.')
        return data
