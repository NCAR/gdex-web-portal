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
                ('icon_name', models.CharField(blank=True, default='', help_text='Icon name class from the fontawesome icon set. See fontawesome version 6 documentation for more info. Either Icon or Icomoon Icon Name can be used to specify an icon for the card.  If both are specified, Icon will take precedence over Icomoon Icon Name.', max_length=50, verbose_name='Icon')),
                ('icomoon_icon_name', models.CharField(blank=True, default='', help_text='(Optional) If using a custom SVG icon from the gdex icomoon set, specify the icon class name here.  Custom icomoon icons can be viewed and added to the gdex custom icon set by adding the SVG to the static/unity/lib/icomoon2/ directory and including the icon class name here. This field is only necessary if the desired icon is not available in the fontawesome icon set.', max_length=50, verbose_name='Icomoon Icon Name')),
                ('text', wagtail.fields.RichTextField(default='', help_text='Body text to be displayed on the home page card.', verbose_name='Body Text')),
                ('card_url', models.URLField(blank=True, help_text='External URL to link to from the card.  If both Card URL and Card Page are provided, Card Page will take precedence.', null=True, verbose_name='Card URL')),
                ('card_page', models.ForeignKey(
                    blank=True,
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
