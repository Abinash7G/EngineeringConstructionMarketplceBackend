# Generated by Django 5.1.4 on 2025-05-11 05:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ersathi', '0056_remove_order_deadline_date_remove_order_fine_amount'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='engineeringconsultingdata',
            options={'verbose_name': 'Engineering Consulting Data', 'verbose_name_plural': 'Engineering Consulting Data'},
        ),
        migrations.AddField(
            model_name='engineeringconsultingdata',
            name='architectural_design',
            field=models.FileField(blank=True, null=True, upload_to='inquiry_files/engineering/architectural/'),
        ),
        migrations.AddField(
            model_name='engineeringconsultingdata',
            name='cost_estimation_files',
            field=models.FileField(blank=True, null=True, upload_to='inquiry_files/engineering/cost_estimation/'),
        ),
        migrations.AddField(
            model_name='engineeringconsultingdata',
            name='rate_analysis',
            field=models.FileField(blank=True, null=True, upload_to='inquiry_files/engineering/rate_analysis/'),
        ),
        migrations.AddField(
            model_name='engineeringconsultingdata',
            name='structural_design',
            field=models.FileField(blank=True, null=True, upload_to='inquiry_files/engineering/structural/'),
        ),
        migrations.AddField(
            model_name='engineeringconsultingdata',
            name='structural_report',
            field=models.FileField(blank=True, null=True, upload_to='inquiry_files/engineering/structural/'),
        ),
    ]
