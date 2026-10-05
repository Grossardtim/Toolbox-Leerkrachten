from django.conf import settings
from django.db import models
from django.db.models import Q

GRADES = [(n, f'{n}e leerjaar') for n in range(1, 8)]
STAGES = [(1, '1e graad'), (2, '2e graad'), (3, '3e graad (inclusief 7e leerjaar)')]

def stage_for_grade(grade):
    return min(3, (grade + 1) // 2) if grade in range(1, 8) else None

class Owned(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    class Meta:
        abstract = True

class Year(Owned):
    name = models.CharField('Schooljaar', max_length=30)
    class Meta:
        ordering = ['-name']
        constraints = [models.UniqueConstraint(fields=['owner', 'name'], name='unique_owner_year')]
    def __str__(self): return self.name

class Subject(Owned):
    year = models.ForeignKey(Year, on_delete=models.PROTECT)
    name = models.CharField('Vak', max_length=100)
    study_directions = models.ManyToManyField('StudyDirection', verbose_name='Studierichtingen', blank=True)
    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(fields=['owner', 'year', 'name'], name='unique_subject')]
    def __str__(self): return self.name

class StudyDirection(Owned):
    name = models.CharField('Studierichting', max_length=150)
    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(fields=['owner', 'name'], name='unique_owner_direction')]
    def __str__(self): return self.name

class Classroom(Owned):
    year = models.ForeignKey(Year, on_delete=models.PROTECT)
    name = models.CharField('Klasnaam', max_length=60)
    direction = models.CharField('Studierichting', max_length=150)
    study_direction = models.ForeignKey(StudyDirection, null=True, on_delete=models.PROTECT, verbose_name='Studierichting')
    grade = models.PositiveSmallIntegerField('Leerjaar', choices=GRADES, null=True)
    subjects = models.ManyToManyField(Subject, blank=True, verbose_name='Vakken')
    archived = models.BooleanField('Gearchiveerd', default=False)
    class Meta:
        ordering = ['study_direction__name', 'name', 'pk']
        constraints = [models.UniqueConstraint(fields=['owner', 'year', 'name'], name='unique_class')]
    def __str__(self): return self.name

    @property
    def direction_name(self):
        return self.study_direction.name if self.study_direction_id else self.direction

class Student(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT, related_name='students')
    name = models.CharField('Naam leerling', max_length=150)
    active = models.BooleanField('Actief in de klas', default=True)
    class Meta: ordering = ['name', 'pk']
    def __str__(self): return self.name

class Goal(Owned):
    study_direction = models.ForeignKey(StudyDirection, null=True, on_delete=models.PROTECT, verbose_name='Studierichting')
    stage = models.PositiveSmallIntegerField('Graad', choices=STAGES, null=True)
    legacy_context = models.JSONField(default=dict, editable=False)
    code = models.CharField('Doelcode', max_length=80)
    title = models.CharField('Leerplandoelstelling', max_length=500)
    archived = models.BooleanField('Gearchiveerd', default=False)
    class Meta: ordering = ['code', 'pk']
    def __str__(self): return f'{self.code} · {self.title}'

class Point(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='points')
    title = models.CharField('Evaluatiepunt', max_length=500)
    position = models.PositiveIntegerField(default=0)
    class Meta: ordering = ['position', 'pk']

class Lesson(Owned):
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    grade = models.PositiveSmallIntegerField('Leerjaar', choices=GRADES, null=True)
    title = models.CharField('Lesonderwerp', max_length=180)
    date = models.DateField('Lesdatum')
    feedback = models.TextField('Klasfeedback', blank=True)
    revision = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ['-date', '-pk']

class LessonStudent(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='roster')
    student = models.ForeignKey(Student, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=150)
    feedback = models.TextField(blank=True)
    class Meta:
        ordering = ['name', 'pk']
        constraints = [models.UniqueConstraint(fields=['lesson', 'student'], name='unique_roster')]

class LessonGoal(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='goals')
    source = models.ForeignKey(Goal, null=True, on_delete=models.SET_NULL)
    code = models.CharField(max_length=80)
    title = models.CharField(max_length=500)
    position = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['position', 'pk']
        constraints = [models.UniqueConstraint(fields=['lesson', 'source'], name='unique_lesson_goal')]

class LessonPoint(models.Model):
    goal = models.ForeignKey(LessonGoal, on_delete=models.CASCADE, related_name='points')
    source_point = models.ForeignKey(Point, null=True, blank=True, on_delete=models.SET_NULL)
    is_direct = models.BooleanField(default=False)
    title = models.CharField(max_length=500)
    position = models.PositiveIntegerField(default=0)
    class Meta: ordering = ['position', 'pk']

class Score(models.Model):
    point = models.ForeignKey(LessonPoint, on_delete=models.CASCADE)
    learner = models.ForeignKey(LessonStudent, on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(n, str(n)) for n in [0, 20, 40, 60, 80]])
    status = models.CharField(max_length=10, default='scored', choices=[('scored', 'Beoordeeld'), ('absent', 'Afwezig')])
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['point', 'learner'], name='unique_score'),
            models.CheckConstraint(condition=(Q(status='scored', value__isnull=False, value__in=[0, 20, 40, 60, 80]) | Q(status='absent', value__isnull=True)), name='valid_score_or_absence'),
        ]

class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=80)
    object_type = models.CharField(max_length=50)
    object_id = models.PositiveBigIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
