from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_homepagesearchsuggestion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homepagesearchsuggestion',
            name='search_term',
            field=models.CharField(
                max_length=25,
                verbose_name='Search Term',
                help_text='Search term displayed under the home page search bar as a search suggestion badge.  For example, "AI Ready Datasets" or "Zarr Format Datasets".',
            ),
        ),
        migrations.AlterField(
            model_name='homepagesearchsuggestion',
            name='search_term_url',
            field=models.CharField(
                max_length=255,
                verbose_name='Search Term URL',
                help_text='Search term URL specified as the GDEX Search URL to link to when the search term is clicked.  This can be a relative URL or absolute URL. For example, a relative URL could be /gsearch/dataset-search/?q=&filter-match-all.tags=AI%20Ready and an absolute URL could be https://gdex.ucar.edu/gsearch/dataset-search/?q=&filter-match-all.tags=AI%20Ready to link to a search for AI-Ready datasets.',
            ),
        ),
    ]
