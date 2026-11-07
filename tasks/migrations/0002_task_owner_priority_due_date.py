from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def assign_owner(apps, schema_editor):
    """Give tasks created before login existed to the first superuser (or first user)."""
    Task = apps.get_model('tasks', 'Task')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    orphans = Task.objects.filter(user__isnull=True)
    if not orphans.exists():
        return

    owner = (
        User.objects.filter(is_superuser=True).order_by('pk').first()
        or User.objects.order_by('pk').first()
    )
    if owner is None:
        raise RuntimeError(
            'Existing tasks need an owner. Create a user first '
            '(python manage.py createsuperuser), then run migrate again.'
        )
    orphans.update(user=owner)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['completed', '-created_at']},
        ),
        migrations.AddField(
            model_name='task',
            name='user',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tasks',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='task',
            name='priority',
            field=models.CharField(
                choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
                default='medium',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='task',
            name='due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.RunPython(assign_owner, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='task',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tasks',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
