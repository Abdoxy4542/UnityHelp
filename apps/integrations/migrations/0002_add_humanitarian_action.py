# Generated manually for Humanitarian Action Info integration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0001_initial'),
    ]

    operations = [
        # Update ExternalDataSource platform choices to include humanitarian_action
        migrations.AlterField(
            model_name='externaldatasource',
            name='platform',
            field=models.CharField(
                choices=[
                    ('hdx', 'Humanitarian Data Exchange'),
                    ('iom_dtm', 'IOM Displacement Tracking Matrix'),
                    ('unhcr', 'UNHCR Refugee Data'),
                    ('fts', 'OCHA Financial Tracking Service'),
                    ('who', 'WHO Health Data'),
                    ('acaps', 'ACAPS Analysis'),
                    ('wfp', 'World Food Programme'),
                    ('fews_net', 'FEWS NET'),
                    ('humanitarian_action', 'Humanitarian Action Info'),
                ],
                max_length=20
            ),
        ),

        # Create HumanitarianActionPlanData model
        migrations.CreateModel(
            name='HumanitarianActionPlanData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_id', models.CharField(max_length=100)),
                ('plan_type', models.CharField(
                    choices=[
                        ('humanitarian_response_plan', 'Humanitarian Response Plan'),
                        ('emergency_appeal', 'Emergency Appeal'),
                        ('regional_response', 'Regional Response'),
                        ('contingency_plan', 'Contingency Plan'),
                        ('general_plan', 'General Plan'),
                    ],
                    max_length=50
                )),
                ('total_requirements_usd', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('funded_amount_usd', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('funding_gap_usd', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('funding_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('target_population', models.CharField(blank=True, max_length=200)),
                ('people_in_need', models.PositiveIntegerField(blank=True, null=True)),
                ('plan_start_date', models.DateField(blank=True, null=True)),
                ('plan_end_date', models.DateField(blank=True, null=True)),
                ('timeframe_description', models.CharField(blank=True, max_length=200)),
                ('sectors', models.JSONField(default=list, help_text='List of humanitarian sectors')),
                ('locations', models.JSONField(default=list, help_text='List of affected locations')),
                ('organizations', models.JSONField(default=list, help_text='List of participating organizations')),
                ('objectives', models.JSONField(default=list, help_text='List of plan objectives')),
                ('crisis_data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='integrations.sudancrisisdata')),
            ],
            options={
                'db_table': 'integrations_humanitarian_action_plan_data',
            },
        ),

        # Add unique constraint
        migrations.AlterUniqueTogether(
            name='humanitarianactionplandata',
            unique_together={('crisis_data', 'plan_id')},
        ),
    ]