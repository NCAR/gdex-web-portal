from datetime import date, timedelta

from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.blocks import BooleanBlock
from wagtail.admin.edit_handlers import (
    FieldPanel,
    MultiFieldPanel,
    InlinePanel,
    StreamFieldPanel,
    PageChooserPanel
)
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail.snippets.edit_handlers import SnippetChooserPanel

class NewsAuthorOrderable(Orderable):
    """ This allows us to select one or more news authors from snippets """
    page = ParentalKey("NewsPage", related_name="news_authors")
    author = models.ForeignKey(
        "NewsAuthor",
        on_delete=models.CASCADE,
    )

    panels = [
        SnippetChooserPanel("author"),
    ]

@register_snippet
class NewsAuthor(models.Model):
    """ News author for snippets """

    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, default='rdahelp@ucar.edu')
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("email"),
                ImageChooserPanel("image"),
            ],
            heading="Name and Email"
        )
    ]

    def __str__(self):
        """ String repr of this class """
        return self.name

    class Meta:
        verbose_name = "News Author"
        verbose_name_plural = "News Authors"

@register_snippet
class DecsStaff(models.Model):
    """ DECS staff members for snippets """

    name = models.CharField(
        max_length=100,
        help_text='DECS staff member name',
    )
    email = models.EmailField(
        max_length=100, 
        default='rdahelp@ucar.edu',
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text='DECS staff image (optional)',
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("email"),
                ImageChooserPanel("image"),
            ],
            heading="Name, Email, and Image"
        )
    ]

    def __str__(self):
        """ String repr of this class """
        return self.name

    class Meta:
        verbose_name = "DECS Staff Member"
        verbose_name_plural = "DECS Staff Members"

@register_snippet
class SocialMedia(models.Model):
    """ Social media links for snippets """

    name = models.CharField(max_length=50)
    related_url = models.URLField(
        blank=False,
        null=False,
        help_text='Link to social media page',
    )
    aria_label=models.CharField(
        max_length=50,
        help_text='Aria label to apply to the <a href> tag',
    )
    icon_style=models.CharField(
        max_length=50,
        default="",
        verbose_name='Icon style',
        help_text="Icon style class to render the social media icon. Specify 'fab' for brands and 'fas' for solid.  See fontawesome version 5 documentation for more info.",
    )
    icon_name=models.CharField(
        max_length=50,
        default="",
        verbose_name='Icon name',
        help_text='Icon name class from the fontawesome icon set',
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("related_url"),
                FieldPanel("aria_label"),
                FieldPanel("icon_style"),
                FieldPanel("icon_name"),
            ]
        )
    ]

    def __str__(self):
        """ String repr of this class """
        return self.name

    class Meta:
        verbose_name = "Social Media Link"
        verbose_name_plural = "Social Media Links"

@register_snippet
class AlertMessage(models.Model):
    """ Alert message for snippets """

    DANGER = 'danger'
    WARNING = 'warning'
    INFO = 'info'
    LEVEL_CHOICES = [
        (DANGER, 'danger'),
        (WARNING, 'warning'),
        (INFO, 'info'),
    ]
    message = RichTextField(blank=False, default="")
    name = models.CharField(max_length=100)
    level = models.CharField(
        max_length=7,
        choices=LEVEL_CHOICES,
        default=INFO,
    )
    related_url = models.URLField(
        blank=True, 
        null=True,
        help_text='Optional.  Related page takes precedence over related URL.',
    )
    related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Optional.  Related page takes precedence over related URL.',
    )
    start_date = models.DateField('Start date', default=date.today())
    end_date = models.DateField('End date', default=date.today())

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("message"),
                FieldPanel("level"),         
            ],
            heading="Alert name, message, and level",
        ),
        MultiFieldPanel(
            [
                PageChooserPanel("related_page"),
                FieldPanel("related_url"),
            ],
            heading="Related URL or page",
        ),
        MultiFieldPanel(
            [
                FieldPanel("start_date"),
                FieldPanel("end_date"),
            ],
            heading="Start and end dates to display message",
        ),
    ]

    def __str__(self):
        """ String repr of this class """
        return self.name

    class Meta:
        verbose_name = "Alert Message"
        verbose_name_plural = "Alert Messages"

class HomePage(Page):
    tagline = models.CharField(max_length=100, blank=False, default="")
    welcome = RichTextField(blank=False, default="")
    search_box_title = models.CharField(max_length=255, blank=False, default="", 
        verbose_name="Search Box Title")
    search_box_placeholder = models.CharField(max_length=255, blank=False, default="", 
        verbose_name="Search Box Placeholder")
    card_1_title = models.CharField(max_length=255, blank=False, default="",
        verbose_name="Title")
    card_1_icon_name = models.CharField(max_length=50, blank=False, default="",
        verbose_name="Icon")
    card_1_text = RichTextField(blank=False, default="",
        verbose_name="Body Text")
    card_1_footer_text = models.CharField(max_length=255, blank=False,
        default="", verbose_name="Footer Text")
    card_1_footer_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    card_2_title = models.CharField(max_length=255, blank=False, default="",
        verbose_name="title")
    card_2_icon_name = models.CharField(max_length=50, blank=False, default="",
        verbose_name="Icon")
    card_2_text = RichTextField(blank=False, default="",
         verbose_name="Body Text")
    card_2_footer_text = models.CharField(max_length=255, blank=False,
        default="", verbose_name="Footer Text")
    card_2_footer_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    card_3_title = models.CharField(max_length=255, blank=False, default="",
        verbose_name="Title")
    card_3_icon_name = models.CharField(max_length=50, blank=False, default="",
        verbose_name="Icon")
    card_3_text = RichTextField(blank=False, default="",
        verbose_name="Body Text")
    card_3_footer_text = models.CharField(max_length=255, blank=False,
        default="", verbose_name="Footer Text")
    card_3_footer_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    content_panels = Page.content_panels + [
        FieldPanel('tagline', classname="collapsible collapsed"),
        FieldPanel('welcome', classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('search_box_title'),
            FieldPanel('search_box_placeholder'),
        ], heading="Search Box", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('card_1_title'),
            FieldPanel('card_1_icon_name'),
            FieldPanel('card_1_text'),
            FieldPanel('card_1_footer_text'),
            PageChooserPanel('card_1_footer_page'),
        ], heading="Card 1", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('card_2_title'),
            FieldPanel('card_2_icon_name'),
            FieldPanel('card_2_text'),
            FieldPanel('card_2_footer_text'),
            PageChooserPanel('card_2_footer_page'),
        ], heading="Card 2", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('card_3_title'),
            FieldPanel('card_3_icon_name'),
            FieldPanel('card_3_text'),
            FieldPanel('card_3_footer_text'),
            PageChooserPanel('card_3_footer_page'),
        ], heading="Card 3", classname="collapsible collapsed"),
    ]
    is_creatable = False

class TaxonomyTerm(Orderable):
    card = ParentalKey('Card', related_name='taxonomyterm', on_delete=models.CASCADE)
    term = models.CharField(max_length=255, blank=True, default="")
    href = models.URLField(blank=True, null=True)
    panels = [
    	FieldPanel('term'),
    	FieldPanel('href')
    ]

class Card(Orderable, ClusterableModel):
    page = ParentalKey('GenericPage', on_delete=models.CASCADE, related_name='cards')
    title = models.CharField(max_length=255, blank=True, default="",
        verbose_name="title")
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    link = models.URLField(
        blank=True, 
        null=True,
        verbose_name="External link",
        help_text="Choose either Related Page, External Link, or Internal link",
    )
    internal_link = models.CharField(
        verbose_name="internal link", 
        max_length=100,
        null=True, 
        blank=True, 
        default="",
        help_text="Choose either Related Page, External Link, or Internal link.  Internal link can include a #hash or querystring appended to the URL.",
    )
    related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Choose either Related Page, External Link, or Internal link",
    )
    link_text = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Provide the text to use for a related page, external URL, or internal link.  Default='LINK' for external URL or internal link, and the page title for related page",
    )
    text = RichTextField(
        features=['h2', 'h3', 'h4', 'bold', 'italic', 'ol', 'ul', 'hr', 'link', 'document-link', 'image', 'embed', 'code', 'blockquote'],
        blank=False, 
        default="",
        verbose_name="Body Text")

    panels = [
        FieldPanel('title'),
        ImageChooserPanel('image'),
        MultiFieldPanel(
            [
                PageChooserPanel('related_page'),
                FieldPanel('link'),
                FieldPanel('internal_link'),
                FieldPanel('link_text'),
            ]
        ),
        FieldPanel('text'),
        InlinePanel('taxonomyterm', label="Taxonomy Terms")
    ]
    
class GenericPage(Page):
    intro = RichTextField(blank=True, default="")
    sidebar = models.BooleanField(default=True)
    table_of_contents = models.BooleanField(default=False)

    #page_options = StreamField([
    #    ('sidebar', BooleanBlock(required=True, help_text='Display With Sidebar')),
    #], block_counts={'sidebar':{'min_num':1,'max_num':1}},
    #   blank=False)

    content_panels = Page.content_panels + [
    #    StreamFieldPanel('page_options'),
        FieldPanel('sidebar'),
        FieldPanel('table_of_contents'),
        FieldPanel('intro'),
    	InlinePanel('cards', label='Cards'),
       
    ]

class StaffPage(Page):
    # Database fields
    body = RichTextField(blank=True)
    mission = RichTextField(blank=True)
    cts_text = RichTextField(blank=True)
    additional_information = RichTextField(blank=True)
 
    # Editor panels configuration
    content_panels = Page.content_panels + [
        FieldPanel('body', classname='full'),
        FieldPanel(
            'mission',
            heading='RDA Mission description',
        ),
        FieldPanel(
            'cts_text',
            heading='CoreTrustSeal acknowledgement',
            classname='collapsible collapsed',
        ),
        FieldPanel('additional_information', classname='full'),
    ]
    
class DocumentationPage(Page):
    header = models.CharField(max_length=100, blank=False, default="")
    sidebar = models.BooleanField(default=True)

    content_panels = Page.content_panels + [
        FieldPanel('sidebar'),
        InlinePanel(
            'links',
            label='Documentation Links',
            classname='collapsible collapsed',
        ),
        InlinePanel(
            'docs',
            label='Documents',
            classname='collapsible collapsed',
        ),
    ]

class DocumentCard(ClusterableModel, Orderable):
    page = ParentalKey(
        'DocumentationPage',
        on_delete=models.CASCADE,
        related_name='docs'
    )
    long_name = models.CharField(
        max_length=255,
        blank=False,
        default="",
        verbose_name="Document long name"
    )
    description = RichTextField(blank=True)
    file_name = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        FieldPanel('long_name'),
        FieldPanel('description'),
        DocumentChooserPanel('file_name')
    ]

class DocumentLink(ClusterableModel, Orderable):
    page = ParentalKey(
        'DocumentationPage',
        on_delete=models.CASCADE,
        related_name='links'
    )
    long_name = models.CharField(
        max_length=255,
        blank=False,
        default="",
        verbose_name="Documentation long name"
    )
    description = RichTextField(
        blank=False,
        default="",
        verbose_name="Documentation description"
    )
    doc_url = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Link to a custom URL"
    )
    doc_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Link to an internal page",
    )
    link_append = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Append to URL",
        help_text="Use this to optionally append a #hash or querystring to the above page's URL.",
    )
    link_text = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Provide the text to use for a custom URL or internal page.  Default=Documentation long name.",
    )

    panels = [
        FieldPanel('long_name'),
        FieldPanel('description'),
        FieldPanel('doc_url'),
        PageChooserPanel('doc_page'),
        FieldPanel('link_append'),
        FieldPanel('link_text'),
    ]

class NewsPage(Page):
    post_date = models.DateField('Post date')
    body = RichTextField(blank=True)
    blogger_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL of the original post on the NCAR RDA Blogger page",
    )
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.FilterField('post_date'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('post_date', classname='full'),
        FieldPanel('body', classname='full'),
        FieldPanel('blogger_url', classname='full'),
        MultiFieldPanel(
            [
                InlinePanel("news_authors", label="Author", min_num=1, max_num=7)
            ],
            heading="Author(s)",
        ),
        ImageChooserPanel('image'),
    ]
    def get_next_sibling(self):
        siblings = list(self.get_siblings().live().specific())
        siblings.sort(key=lambda k: k.post_date)
        for i,page in enumerate(siblings):
            if page.url == self.url:
                if i == len(siblings)-1:
                    return None
                else:
                    return siblings[(i+1)]
        
    def get_prev_sibling(self):
        siblings = list(self.get_siblings().live().specific())
        siblings.sort(key=lambda k: k.post_date)
        for i,page in enumerate(siblings):
            if page.url == self.url:
                if i == 0:
                    return None
                else:
                    return siblings[(i-1)]

    class Meta:
        ordering = ['-post_date']

class NewsHome(Page):
    subpage_types = [ 'home.NewsPage' ]
    title_description = RichTextField(blank=True)
    content_panels = Page.content_panels + [
        FieldPanel('title_description'),
    ]
    
    def get_recent_posts(self, num=6):
        """ Returns the most recent news posts (default 6)"""

        recent_posts = NewsPage.objects.live().order_by('post_date').reverse()[:num]

        return recent_posts

    def get_older_posts(self, num=6):
        """ Returns news posts older than the most num recent posts 
            (default num=6)
        """

        older_posts = NewsPage.objects.live().order_by('post_date').reverse()[num:] 

        year_sorted_posts = {}
        for post in older_posts:
            post_year = post.post_date.year
            if post_year not in year_sorted_posts:
                year_sorted_posts[post_year] = [post]
            else:
                year_sorted_posts[post_year].append(post)
        return year_sorted_posts

class MetricsPage(Page):
    body = RichTextField(blank=True)
    content_panels = Page.content_panels + [
    FieldPanel('body', classname='full'),
    ]

class RedirectPage(Page):
    redirect_url = models.URLField(
        blank=False,
        null=False,
        verbose_name="Redirect URL",
    )
    content_panels = Page.content_panels + [
        FieldPanel('redirect_url'),
    ]

class ManPage(Page):
    body=RichTextField(
        features=['h2', 'h3', 'h4', 'bold', 'italic', 'ol', 'ul', 'hr', 'link', 'document-link', 'image', 'embed', 'code', 'blockquote'],
        blank=True,
    )
    content_panels = Page.content_panels + [
        FieldPanel('body')
    ]

@register_snippet
class DataLicense(models.Model):
    """ Data license information for snippets """

    id = models.CharField(
        max_length=50,
        primary_key=True,
        help_text="Short name for the data license",
    )
    url = models.URLField(
        blank=False,
        null=False,
        verbose_name="Link to data license",
    )
    img_url = models.URLField(
        blank=False,
        null=False,
        verbose_name="Link to image for data license",
    )
    name = models.CharField(
        max_length=255,
        help_text="Full name of data license",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("id"),
                FieldPanel("url"),
                FieldPanel("img_url"),
                FieldPanel("name"),
            ]
        )
    ]
