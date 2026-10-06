from .models import Goal, LessonGoal, LessonPoint, Score, stage_for_grade

def goals_for_lesson(lesson, viewer=None):
    stage = stage_for_grade(lesson.grade)
    direction = lesson.classroom.study_direction_id
    if stage is None or direction is None:
        return Goal.objects.none()
    from accounts.access import visible_records
    catalog = Goal.objects.all()
    return catalog.filter(study_direction_id=direction,
                               stage=stage, archived=False)

def snapshot_goal(lesson, source, selected_points=None):
    """Append selected subgoals without replacing snapshots or existing scores."""
    target, _ = LessonGoal.objects.get_or_create(lesson=lesson, source=source,
        defaults={'code': source.code, 'title': source.title, 'position': lesson.goals.count()})
    points = list(source.points.all() if selected_points is None else selected_points)
    if any(p.goal_id != source.pk for p in points):
        raise ValueError('Een subdoel hoort niet bij de gekozen BK.')
    existing = list(target.points.all())
    position = max((p.position for p in existing), default=-1) + 1
    if not source.points.exists():
        if not any(p.is_direct for p in existing):
            LessonPoint.objects.create(goal=target, title=source.title, position=position, is_direct=True)
    else:
        for p in points:
            if any(x.source_point_id == p.pk for x in existing):
                continue
            LessonPoint.objects.create(goal=target, source_point=p, title=p.title, position=position)
            position += 1
    return target

def metric(values, possible):
    absent = sum(v == 'absent' for v in values)
    values = [v for v in values if isinstance(v, int)]
    return {'total': sum(values) if values else None,
            'average': sum(values) / len(values) if values else None,
            'maximum': len(values) * 80, 'count': len(values), 'possible': possible, 'absent': absent}

def display_goal_groups(groups):
    """Group only the lesson presentation; keep every goal, point and score ID."""
    titles = {}
    for group in groups:
        key = ' '.join(group['goal'].title.split()).casefold()
        titles.setdefault(key, []).append(group)

    def combined(metrics):
        count = sum(m['count'] for m in metrics)
        total = sum(m['total'] or 0 for m in metrics)
        return {'count': count, 'total': total if count else None,
                'average': total / count if count else None, 'maximum': count * 80,
                'possible': sum(m['possible'] for m in metrics),
                'absent': sum(m['absent'] for m in metrics)}

    result = []
    for members in titles.values():
        rows_with_points = []
        for m in members:
            for row in m['rows']:
                rows_with_points.append({**row, 'code': m['goal'].code, 'point_id': row['point'].pk})
        result.append({
            'title': members[0]['goal'].title, 'goal': members[0]['goal'],
            'members': members, 'merged': len(members) > 1,
            'ids': ','.join(str(m['goal'].pk) for m in members),
            'rows': rows_with_points,
            'students': [combined([m['students'][i] for m in members])
                         for i in range(len(members[0]['students']))],
        })
    return result


def lesson_report(lesson, submitted=None):
    learners = list(lesson.roster.all())
    goals = list(lesson.goals.prefetch_related('points'))
    scores = {(s.point_id, s.learner_id): ('absent' if s.status == 'absent' else s.value) for s in
              Score.objects.filter(point__goal__lesson=lesson)}
    all_values = []
    per_student = {s.pk: [] for s in learners}
    groups = []
    total_points = 0
    for goal in goals:
        points = list(goal.points.all())
        rows, group_values = [], []
        group_student = {s.pk: [] for s in learners}
        total_points += len(points)
        for point in points:
            cells = []
            for learner in learners:
                field = f'score_{point.pk}_{learner.pk}'
                value = scores.get((point.pk, learner.pk))
                # Keep submitted values visible on validation/conflict; never save implicitly.
                display = submitted.get(field, '') if submitted is not None else (str(value) if value is not None else '')
                cells.append({'name': field, 'value': display, 'student': learner.name, 'point': point.title})
                group_values.append(value)
                group_student[learner.pk].append(value)
                per_student[learner.pk].append(value)
                all_values.append(value)
            rows.append({'point': point, 'cells': cells})
        groups.append({'goal': goal, 'rows': [{**row, 'point_id': row['point'].pk} for row in rows],
            'students': [metric(group_student[s.pk], len(points)) for s in learners],
            'class_metric': metric(group_values, len(points) * len(learners))})
    for learner in learners:
        learner.display_feedback = (submitted.get(f'feedback_{learner.pk}', '')
                                    if submitted is not None else learner.feedback)
    return {'learners': learners, 'groups': groups,
        'student_metrics': [{'learner': s, 'metric': metric(per_student[s.pk], total_points)} for s in learners],
        'class_metric': metric(all_values, total_points * len(learners)),
        'total_points': total_points, 'levels': ['0', '20', '40', '60', '80']}
