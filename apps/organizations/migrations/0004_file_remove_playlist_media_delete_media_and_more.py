from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organizations', '0003_remove_organization_db_name'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Media',
            new_name='File',
        ),
        migrations.RenameField(
            model_name='file',
            old_name='media_id',
            new_name='file_id',
        ),
        migrations.RenameField(
            model_name='playlist',
            old_name='media',
            new_name='file',
        ),
    ]
