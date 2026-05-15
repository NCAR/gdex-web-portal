import django.db.models.deletion
import modelcluster.fields
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0007_alter_homepagesearchsuggestion_fields'),
        ('wagtailcore', '0094_alter_page_locale'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeaturedCard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('title', models.CharField(default='', help_text='Title of the card to be displayed on the home page.', max_length=255, verbose_name='Title')),
                ('icon_name', models.CharField(default='', help_text='Icon name class from the fontawesome icon set.  See fontawesome version 5 documentation for more info.', max_length=50, verbose_name='Icon')),
                ('text', wagtail.fields.RichTextField(default='', help_text='Body text to be displayed on the home page card.', verbose_name='Body Text')),
                ('card_url', models.URLField(blank=True, help_text='External URL to link to from the card.  If both Card URL and Card Page are provided, Card Page will take precedence.', null=True, verbose_name='Card URL')),
                ('card_page', models.ForeignKey(
                    blank=False,
                    help_text='Internal page to link to from the card. If both Card Page and Card URL are provided, Card Page will take precedence.',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to='wagtailcore.page',
                    verbose_name='Card Page',
                )),
                ('page', modelcluster.fields.ParentalKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='featured_cards',
                    to='home.homepage',
                )),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
    ]
