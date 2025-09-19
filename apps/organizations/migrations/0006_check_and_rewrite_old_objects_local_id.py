from django.db import migrations


def populate_local_ids(apps, schema_editor):
    Device = apps.get_model("organizations", "Device")
    File = apps.get_model("organizations", "File")
    Playlist = apps.get_model("organizations", "Playlist")

    # Device uchun
    for org_id in Device.objects.values_list("organization_id", flat=True).distinct():
        devices = Device.objects.filter(organization_id=org_id).order_by("id")
        counter = 1
        for d in devices:
            d.local_id = counter
            d.save(update_fields=["local_id"])
            counter += 1

    # File uchun
    for org_id in File.objects.values_list("organization_id", flat=True).distinct():
        files = File.objects.filter(organization_id=org_id).order_by("file_id")
        counter = 1
        for f in files:
            f.local_id = counter
            f.save(update_fields=["local_id"])
            counter += 1

    # Playlist uchun
    for org_id in Playlist.objects.values_list("organization_id", flat=True).distinct():
        playlists = Playlist.objects.filter(organization_id=org_id).order_by("id")
        counter = 1
        for p in playlists:
            p.local_id = counter
            p.save(update_fields=["local_id"])
            counter += 1


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0005_alter_file_options_device_local_id_file_local_id_and_more"),  # oxirgi migration nomini yozasiz
    ]

    operations = [
        migrations.RunPython(populate_local_ids, migrations.RunPython.noop),
    ]
