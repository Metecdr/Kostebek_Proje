from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('magaza', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='magazaurun',
            name='avatar_emoji',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Avatar Emoji'),
        ),
    ]
