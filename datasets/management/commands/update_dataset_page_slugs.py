from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from dataset_description.models import DatasetDescriptionPage
from wagtail.core.models import Page
import re

class Command(BaseCommand):
    help = 'Updates the Dataset Description Page slugs, url_path, and page title to the new dataset ID format.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dsid', 
            type=str,
            required=False,
            help="Dataset number or ID as nnn.n or dsnnn.n.  If omitted, all dataset pages will be updated.")

    def handle(self, *args, **options):
        if not settings.NEW_DATASET_ID:
            raise CommandError('Page slugs for dataset description pages cannot be updated prior to July 30, 2024.')

        if options['dsid']:
            filter_slug = self.format_slug(options['dsid'])
            ds_pages = DatasetDescriptionPage.objects.filter(slug=filter_slug)
        else:
            ds_pages = DatasetDescriptionPage.objects.filter(slug__regex="^ds\d{3}-\d{1}")

        for ds_page in ds_pages:
            slug = ds_page.slug
            url_path = ds_page.url_path
            page_ptr_id = ds_page.page_ptr_id
            title = ds_page.title
            ms = re.match(r'^ds(\d{3})-(\d{1})$', slug)
            if ms:
                new_slug = 'd{:03d}{:03d}'.format(int(ms.group(1)), int(ms.group(2)))
                new_url_path = re.sub('ds\d{3}-\d{1}', new_slug, url_path)
                new_title = re.sub('ds\d{3}\.\d{1}', new_slug, title)
                # self.stdout.write('Old page slug: {}, new slug: {}'.format(slug, new_slug))
                # self.stdout.write('Old url_path: {}, new url_path: {}'.format(url_path, new_url_path))
                self.stdout.write('Page ID: {}'.format(page_ptr_id))
                Page.objects.filter(id=page_ptr_id).update(slug=new_slug, url_path=new_url_path, title=new_title)
                self.stdout.write('Dataset page slug {} successfully updated to {}'.format(slug, new_slug))
                self.stdout.write('Dataset page url_path {} successfully updated to {}'.format(url_path, new_url_path))
                self.stdout.write('Dataset title {} successfully updated to {}.'.format(title, new_title))
            else:
                self.stdout.write('Dataset page slug {} already updated or not in the format dsnnn-n.'.format(slug))

    def format_slug(self, dsid):
        """ 
        Returns a dataset page slug formatted in the legacy format as 'dsnnn-n' 
        """
        # check for format 'dnnnnnn'
        ms = re.match(r'^([a-z]{1})(\d{3})(\d{3})$', dsid)
        if ms:
            return 'ds{:03d}-{}'.format(int(ms.group(2)), int(ms.group(3)))
    
        # check for legacy format 'dsnnn.n', 'dsnnn-n', 'nnn.n', and
        # 'nnn-n'.
        ms = re.match(r'^(ds)?(\d{3})(-|\.)(\d{1})$', dsid)
        if ms:
            return 'ds{}-{}'.format(ms.group(2), ms.group(4))
        
        if not ms:
            raise CommandError('Unknown dsid: {}'.format(dsid))
