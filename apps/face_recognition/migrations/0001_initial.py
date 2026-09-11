from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("employees", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FaceProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("descriptor", models.JSONField(help_text="128-dimensional face embedding")),
                ("sample_count", models.PositiveSmallIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                ("employee", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="face_profile", to="employees.employee")),
                ("registered_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="face_registrations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "face_profile"},
        ),
        migrations.CreateModel(
            name="FaceScanLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("result", models.CharField(choices=[("MATCHED","Matched — attendance marked"),("NO_MATCH","No match found"),("DUPLICATE","Already checked in today"),("ERROR","Processing error")], max_length=20)),
                ("distance", models.FloatField(blank=True, null=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("note", models.CharField(blank=True, max_length=255)),
                ("employee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="face_scan_logs", to="employees.employee")),
            ],
            options={"db_table": "face_scan_log", "ordering": ["-created_at"]},
        ),
    ]
