from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from dataset_provenance.models import DatasetProvenancePage
from dataset_citation.models import DatasetCitationPage
import re

class Command(BaseCommand):
    help = 'Updates the dataset provenance and citation page url_path and page title to the new dataset ID format.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dsid', 
            type=str,
            required=False,
            help="Dataset number or ID as dnnnnnn.  If omitted, all dataset pages will be updated.")

    def handle(self, *args, **options):
        if not settings.NEW_DATASET_ID:
            raise CommandError('Page slugs for dataset description pages cannot be updated prior to July 30, 2024.')

        if options['dsid']:
            pattern = re.compile(r"^d\d{6}$")
            if not pattern.match(options['dsid']):
                raise CommandError("invalid dsid value: {}".format(options['dsid']))

            filter_dsid = options['dsid']
            provenance_pages = DatasetProvenancePage.objects.filter(dsid=filter_dsid)
            citation_pages = DatasetCitationPage.objects.filter(dsid=filter_dsid)
        else:
            provenance_pages = DatasetProvenancePage.objects.filter(dsid__regex="^d\d{6}$")
            citation_pages = DatasetCitationPage.objects.filter(dsid__regex="^d\d{6}$")

        for provenance_page in provenance_pages:
            dsid = provenance_page.dsid
            url_path = provenance_page.url_path
            title = provenance_page.title
            
            new_url_path = re.sub('ds\d{3}-\d{1}', dsid, url_path)
            new_title = re.sub('ds\d{3}\.\d{1}', dsid, title)

            self.stdout.write('Old provenance url_path: {}, new provenance url_path: {}'.format(url_path, new_url_path))
            self.stdout.write('Old provenance title: {}, new provenance title: {}'.format(title, new_title))

            # DatasetProvenancePage.objects.filter(dsid=dsid).update(url_path=new_url_path, title=new_title)
            # self.stdout.write('Dataset provenance url_path {} successfully updated to {}'.format(url_path, new_url_path))
            # self.stdout.write('Dataset provenance title {} successfully updated to {}.'.format(title, new_title))

        for citation_page in citation_pages:
            dsid = citation_page.dsid
            url_path = citation_page.url_path
            title = citation_page.title
            
            new_url_path = re.sub('ds\d{3}-\d{1}', dsid, url_path)
            new_title = re.sub('ds\d{3}\.\d{1}', dsid, title)

            self.stdout.write('Old citation url_path: {}, new citation url_path: {}'.format(url_path, new_url_path))
            self.stdout.write('Old citation title: {}, new citation title: {}'.format(title, new_title))

            # DatasetCitationPage.objects.filter(dsid=dsid).update(url_path=new_url_path, title=new_title)
            # self.stdout.write('Dataset citation url_path {} successfully updated to {}'.format(url_path, new_url_path))
            # self.stdout.write('Dataset citation title {} successfully updated to {}.'.format(title, new_title))
