# Generated manually to create combo adjust tables directly

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cocktail", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecipeComboAdjustResult",
            fields=[
                (
                    "plan_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("snapshot_id", models.CharField(max_length=100)),
                ("recipe_id", models.CharField(max_length=100)),
                ("target_canonical_id", models.CharField(max_length=100)),
                ("candidate_canonical_id", models.CharField(max_length=100)),
                ("repair_canonical_id", models.CharField(max_length=100, null=True)),
                ("repair_role", models.CharField(max_length=100, null=True)),
                ("repair_factor", models.FloatField(default=1.0)),
                ("old_sqe_total", models.FloatField()),
                ("single_sqe_total", models.FloatField()),
                ("combo_sqe_total", models.FloatField()),
                ("delta_sqe_single", models.FloatField()),
                ("delta_sqe_combo", models.FloatField()),
                ("delta_synergy_combo", models.FloatField()),
                ("delta_conflict_combo", models.FloatField()),
                ("delta_balance_combo", models.FloatField()),
                ("accept_flag", models.BooleanField(default=False)),
                ("reason_code", models.CharField(max_length=100, null=True)),
                ("explanation", models.TextField(null=True)),
                ("plan_json", models.JSONField(null=True)),
                ("rank_no", models.IntegerField()),
                ("model_version", models.CharField(max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "recipe_combo_adjust_result",
            },
        ),
        migrations.CreateModel(
            name="RecipeComboAdjustStep",
            fields=[
                (
                    "step_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("plan_id", models.IntegerField()),
                ("step_no", models.IntegerField()),
                ("op_type", models.CharField(max_length=50)),
                ("target_ingredient", models.CharField(max_length=255)),
                ("target_canonical", models.CharField(max_length=100)),
                ("candidate_ingredient", models.CharField(max_length=255, null=True)),
                ("candidate_canonical", models.CharField(max_length=100, null=True)),
                ("amount_factor", models.FloatField(null=True)),
                ("role_info", models.CharField(max_length=100)),
                ("before_sqe_total", models.FloatField()),
                ("after_sqe_total", models.FloatField()),
                ("delta_sqe", models.FloatField()),
                ("note", models.TextField(null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "recipe_combo_adjust_step",
            },
        ),
        migrations.AddIndex(
            model_name="recipecomboadjustresult",
            index=models.Index(fields=["recipe_id", "snapshot_id"], name="cocktail_rec_recipe_id_sna_idx"),
        ),
        migrations.AddIndex(
            model_name="recipecomboadjustresult",
            index=models.Index(fields=["recipe_id", "target_canonical_id"], name="cocktail_rec_recipe_id_tar_idx"),
        ),
        migrations.AddIndex(
            model_name="recipecomboadjustresult",
            index=models.Index(fields=["recipe_id", "accept_flag"], name="cocktail_rec_recipe_id_acc_idx"),
        ),
        migrations.AddIndex(
            model_name="recipecomboadjustresult",
            index=models.Index(fields=["rank_no"], name="cocktail_rec_rank_no_idx"),
        ),
        migrations.AddIndex(
            model_name="recipecomboadjustresult",
            index=models.Index(fields=["recipe_id", "rank_no"], name="cocktail_rec_recipe_id_ran_idx"),
        ),
        migrations.AddIndex(
            model_name="recipecomboadjuststep",
            index=models.Index(fields=["plan_id", "step_no"], name="cocktail_ste_plan_id_ste_idx"),
        ),
    ]
