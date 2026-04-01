# Generated manually to add LlmCanonicalMap model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cocktail", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LlmCanonicalMap",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("src_ingredient_id", models.IntegerField()),
                ("src_name_norm", models.CharField(max_length=255)),
                ("canonical_id", models.IntegerField()),
                ("canonical_name", models.CharField(max_length=255)),
                ("canonical_name_zh", models.CharField(max_length=255, null=True)),
                ("confidence", models.FloatField()),
                ("provider", models.CharField(max_length=100)),
                ("model", models.CharField(max_length=100, null=True)),
                ("rationale", models.TextField(null=True)),
                ("status", models.CharField(max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("src_image_path", models.CharField(max_length=500, null=True)),
            ],
            options={
                "db_table": "llm_canonical_map",
            },
        ),
    ]
