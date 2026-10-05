from .models import User


def visible_owner_ids(user):
    if user.is_superuser or user.view_all_teachers:
        return User.objects.values_list('pk', flat=True)
    return [user.pk, *user.visible_teachers.values_list('pk', flat=True)]


def visible_records(model, user):
    from evaluations.models import Student, Lesson
    if model is not Lesson:
        return model.objects.all()
    field = 'classroom__owner_id__in' if model is Student else 'owner_id__in'
    return model.objects.filter(**{field: visible_owner_ids(user)})
