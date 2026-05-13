import django.db.models.deletion
import modelcluster.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_alter_alertmessage_end_date_and_more'),
        ('wagtailcore', '0094_alter_page_locale'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomePageSearchSuggestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('search_term', models.CharField(max_length=25, verbose_name='Search term displayed under the home page search bar as a search suggestion badge.  For example, "AI Ready Datasets" or "Zarr Format Datasets".')),
                ('search_term_url', models.CharField(max_length=255, verbose_name='Search term URL specified as the GDEX Search URL to link to when the search term is clicked.  This can be a relative URL or absolute URL. For example, a relative URL could be /gsearch/dataset-search/?q=&filter-match-all.tags=AI%20Ready and an absolute URL could be https://gdex.ucar.edu/gsearch/dataset-search/?q=&filter-match-all.tags=AI%20Ready to link to a search for AI-Ready datasets.')),
                ('page', modelcluster.fields.ParentalKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='search_suggestions',
                    to='home.homepage',
                )),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
    ]
