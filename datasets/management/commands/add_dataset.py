from django.core.management.base import BaseCommand

from wagtail.models import Page
from datasets.models import DatasetsPage
from dataset_description.models import DatasetDescriptionPage
from dataset_citation.models import DatasetCitationPage
from dataset_provenance.models import DatasetProvenancePage
from home.utils import slug_list


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('dsid', type=str, help="dataset ID as dnnnnnn")

    def handle(self, *args, **options):
        dsid = options['dsid']
        if len(dsid) != 7 or dsid[0] != "d":
            raise RuntimeError("bad dataset number")

        slist = slug_list(dsid)
        qs = Page.objects.type(DatasetDescriptionPage).filter(slug__in=slist)
        if len(qs) == 1:
            if len(qs.live()) == 0:
                qs.first().specific.live = True

            qs.first().specific.slug = dsid
            qs.first().specific.url_path = "/home/datasets/" + dsid
            qs.first().specific.title = "NCAR Dataset " + dsid
            qs.first().specific.save_revision().publish()
            self.stdout.write("Republished dataset description.")
            found_citation = False
            for slug in slist:
                cqs = Page.objects.type(DatasetCitationPage).filter(url_path="/home/datasets/" + slug + "/citation/")
                if len(cqs) == 1:
                    found_citation = True
                    if len(cqs.live()) == 0:
                        cqs.first().specific.live = True

                    cqs.first().specific.url_path = "/home/datasets/" + dsid + "/citation/"
                    cqs.first().specific.title = "NCAR Dataset " + dsid + " Citation"
                    cqs.first().specific.save_revision().publish()
                    self.stdout.write("Republished dataset citation page.")
                    break

            if not found_citation:
                self.add_citation_page(qs[0], dsid)

            found_provenance = False
            for slug in slist:
                pqs = Page.objects.type(DatasetProvenancePage).filter(url_path="/home/datasets/" + slug + "/provenance/")
                if len(pqs) == 1:
                    found_provenance = True
                    if len(pqs.live()) == 0:
                        pqs.first().specific.live = True

                    pqs.first().specific.url_path = "/home/datasets/" + dsid + "/provenance/"
                    pqs.first().specific.title = "NCAR Dataset " + dsid + " Provenance"
                    pqs.first().specific.save_revision().publish()
                    self.stdout.write("Republished dataset provenance page.")
                    break

            if not found_provenance:
                self.add_provenance_page(qs[0], dsid)

            return

        if len(qs) > 1:
            self.stderr.write("Error - multiple datasets found with this ID.")
            return

        page = Page.objects.type(DatasetsPage).first()
        new_description = DatasetDescriptionPage(
            title="NCAR Dataset " + dsid,
            slug=dsid,
            dsid=dsid,
            dstype=" ",
            dstitle=" ",
            abstract=" ",
            temporal={'full': ""},
            variables=[""],
            levels=[],
            contributors=[""],
            volume={'full': ""},
            data_formats=[""],
            data_license={
                'url': "https://creativecommons.org/licenses/by/4.0/legalcode",
                'name': "Creative Commons Attribution 4.0 International License",
                'img_url': "https://i.creativecommons.org/l/by/4.0/88x31.png",
            },
        )

        self.stdout.write(
            "Creating child " + new_description.slug + " of datasets ..."
        )
        new_child = page.add_child(instance=new_description)

        self.stdout.write(
            "Publishing " + new_description.slug + " as child of datasets ..."
        )
        new_child.save_revision().publish()
        self.add_citation_page(new_child, dsid)
        self.add_provenance_page(new_child, dsid)

        self.stdout.write("Done successfully.")

    def add_citation_page(self, page, dsid):
        new_citation = DatasetCitationPage(
            title="NCAR Dataset " + dsid + " Citation",
            slug="citation",
            dsid=dsid,
        )

        self.stdout.write(
            "Creating citation child of dataset " + dsid + " ..."
        )
        new_child = page.add_child(instance=new_citation)

        self.stdout.write(
            "Publishing citation as child of dataset " + dsid + " ..."
        )
        new_child.save_revision().publish()

    def add_provenance_page(self, page, dsid):
        new_provenance = DatasetProvenancePage(
            title="NCAR Dataset " + dsid + " Provenance",
            slug="provenance",
            dsid=dsid,
        )
        self.stdout.write("Creating provenance child of dataset " + dsid + " ...")
        new_child = page.add_child(instance=new_provenance)
        self.stdout.write("Publishing provenance as child of dataset " + dsid + " ...")
        new_child.save_revision().publish()
