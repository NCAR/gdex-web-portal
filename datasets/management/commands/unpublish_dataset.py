from django.core.management.base import BaseCommand

from wagtail.core.models import Page
from datasets.models import DatasetsPage
from dataset_description.models import DatasetDescriptionPage
from dataset_citation.models import DatasetCitationPage
from dataset_provenance.models import DatasetProvenancePage
from home.utils import slug_list


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('dsid', type=str, help="dataset ID as dnnnnnn")

    def handle(self, *args, **options):
       if len(options['dsid']) != 7 or options['dsid'][0] != 'd':
           raise RuntimeError("bad dataset number")

       pages_to_unpublish = (
           DatasetDescriptionPage,
           DatasetCitationPage,
           DatasetProvenancePage,
       )
       num_unpublished = 0
       for slug in slug_list(options['dsid']):
           qs = Page.objects.type(*pages_to_unpublish).filter(url_path__contains=slug).live()
           if len(qs) > 0:
               qs.unpublish()
               num_unpublished += len(qs)

       self.stdout.write("Success: unpublished " + str(num_unpublished) + " of " + str(len(pages_to_unpublish)))
