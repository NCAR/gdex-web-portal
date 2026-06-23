from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField, StreamField
from wagtail.blocks import BooleanBlock
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    InlinePanel,
    PageChooserPanel
)
from wagtail.search import index
from wagtail.snippets.models import register_snippet

class GDEXPage(Page):
    """ Subclass of wagtail.models.Page for GDEX pages to share common fields """

    # explicitly define the reverse relation name so this page can be inherited
    page_ptr = models.OneToOneField(
        Page,
        on_delete=models.CASCADE,
        parent_link=True,
        related_name='%(app_label)s_%(class)s_related',
    )
    menu_title = models.CharField(max_length=50, blank=True, default="",
        help_text='Short title to use in the navigation bar menu.  If blank, the page title will be used.')

    content_panels = Page.content_panels + [
        FieldPanel('menu_title'),
    ]

class NewsAuthorOrderable(Orderable):
    """ This allows us to select one or more news authors from snippets """
    page = ParentalKey("NewsPage", related_name="news_authors")
    author = models.ForeignKey(
        "NewsAuthor",
        on_delete=models.CASCADE,
    )

    panels = [
        FieldPanel("author"),
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
                FieldPanel("image"),
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
        help_text='DECS staff member full name',
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
                FieldPanel("image"),
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
    action_label = models.CharField(
        max_length=100,
        default='Learn More',
        blank=True,
        help_text='Specify label for related link or URL'
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
                FieldPanel("action_label"),
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

class HomePageSearchSuggestion(Orderable):
    """ Search suggestions for the home page search bar """
    page = ParentalKey('HomePage', related_name='search_suggestions', on_delete=models.CASCADE)
    search_term = models.CharField(max_length=25, verbose_name='Search Term', help_text='Search term displayed under the home page search bar as a search suggestion badge.  For example, "AI Ready Datasets" or "Zarr Format Datasets".')
    search_term_url = models.CharField(max_length=255, verbose_name='Search Term URL', help_text='Search term URL specified as the GDEX Search URL to link to when the search term is clicked.  This can be a relative URL or absolute URL. For example, a relative URL could be /gsearch/dataset-search/?q=&filter-match-all.tags=AI%20Ready and an absolute URL could be https://gdex.ucar.edu/gsearch/dataset-search/?q=&filter-match-all.tags=AI%20Ready to link to a search for AI-Ready datasets.')

    panels = [
        FieldPanel('search_term'),
        FieldPanel('search_term_url'),
    ]

class FeaturedCard(Orderable):
    """ Featured cards for the home page highlighting popular content with links """
    page = ParentalKey('HomePage', related_name='featured_cards', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=False, default="",
        verbose_name="Title", help_text="Title of the card to be displayed on the home page.")
    icon_name = models.CharField(
        max_length=50, 
        blank=True, 
        default="",
        verbose_name="Icon", 
        help_text="Icon name class from the fontawesome icon set. See fontawesome version 6 documentation for more info. Either Icon or Icomoon Icon Name can be used to specify an icon for the card.  If both are specified, Icon will take precedence over Icomoon Icon Name."
        )
    icomoon_icon_name = models.CharField(
        max_length=50, 
        blank=True, 
        default="", 
        verbose_name="Icomoon Icon Name", 
        help_text="(Optional) If using a custom SVG icon from the gdex icomoon set, specify the icon class name here.  Custom icomoon icons can be viewed and added to the gdex custom icon set by adding the SVG to the static/unity/lib/icomoon2/ directory and including the icon class name here. This field is only necessary if the desired icon is not available in the fontawesome icon set."
        ) 
    text = RichTextField(
        blank=False, 
        default="",
        verbose_name="Body Text", 
        help_text="Body text to be displayed on the home page card."
        )
    card_url = models.URLField(
        blank=True, 
        null=True, 
        verbose_name="Card URL", 
        help_text="External URL to link to from the card.  If both Card URL and Card Page are provided, Card Page will take precedence."
        )
    card_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Card Page",
        help_text="Internal page to link to from the card. If both Card Page and Card URL are provided, Card Page will take precedence.",
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('icon_name'),
        FieldPanel('icomoon_icon_name'),
        FieldPanel('text'),
        FieldPanel('card_url'),
        PageChooserPanel('card_page'),
    ]

    def clean(self):
        super().clean()
        if not self.card_page and not self.card_url:
            raise ValidationError('Either Card Page or Card URL must be set.')
        if not self.icon_name and not self.icomoon_icon_name:
            raise ValidationError('Either Icon or Icomoon Icon Name must be set.')

class HomePage(Page):
    """ Home page model with fields for the home page search box and featured cards """
    tagline = models.CharField(max_length=100, blank=False, default="")
    welcome = RichTextField(blank=False, default="")
    search_box_title = models.CharField(max_length=255, blank=False, default="",
        verbose_name="Search Box Title")
    search_box_placeholder = models.CharField(max_length=255, blank=False, default="",
        verbose_name="Search Box Placeholder")
    
    content_panels = Page.content_panels + [
        FieldPanel('tagline', classname="collapsible collapsed"),
        FieldPanel('welcome', classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('search_box_title'),
            FieldPanel('search_box_placeholder'),
        ], heading="Search Box", classname="collapsible collapsed"),
        MultiFieldPanel([
            InlinePanel('search_suggestions', label='Search suggestion'),
        ], heading="Search suggestions", classname="collapsible collapsed"),
        MultiFieldPanel([
            InlinePanel('featured_cards', label='Featured card'),
        ], heading="Featured cards", classname="collapsible collapsed"),
    ]
    is_creatable = False

class TestHomePageSearchSuggestion(Orderable):
    """ Search suggestions for the TestHomePage search bar """
    page = ParentalKey('TestHomePage', related_name='search_suggestions', on_delete=models.CASCADE)
    search_term = models.CharField(max_length=25, verbose_name='Search Term', help_text='Search term displayed under the home page search bar as a search suggestion badge.  For example, "AI Ready Datasets" or "Zarr Format Datasets".')
    search_term_url = models.CharField(max_length=255, verbose_name='Search Term URL', help_text='Search term URL specified as the GDEX Search URL to link to when the search term is clicked.  This can be a relative URL or absolute URL. For example, a relative URL could be /gsearch/dataset-search/?q=&filter-match-all.tags=AI%20Ready and an absolute URL could be https://gdex.ucar.edu/gsearch/dataset-search/?q=&filter-match-all.tags=AI%20Ready to link to a search for AI-Ready datasets.')
    description = models.CharField(max_length=100, blank=True, default="", verbose_name='Search Term Description', help_text='Optional short description of the search term to be displayed under the search term badge.  For example, "Datasets prepared for AI/ML applications" or "Cloud-optimized array data".')

    panels = [
        FieldPanel('search_term'),
        FieldPanel('search_term_url'),
        FieldPanel('description'),
    ]

class TestHomePageFeaturedCard(Orderable):
    """ Featured cards for the TestHomePage highlighting popular content with links """
    page = ParentalKey('TestHomePage', related_name='featured_cards', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=False, default="",
        verbose_name="Title", help_text="Title of the card to be displayed on the home page.")
    icon_name = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Icon",
        help_text="Icon name class from the fontawesome icon set. See fontawesome version 6 documentation for more info. Either Icon or Icomoon Icon Name can be used to specify an icon for the card.  If both are specified, Icon will take precedence over Icomoon Icon Name."
        )
    icomoon_icon_name = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Icomoon Icon Name",
        help_text="(Optional) If using a custom SVG icon from the gdex icomoon set, specify the icon class name here.  Custom icomoon icons can be viewed and added to the gdex custom icon set by adding the SVG to the static/unity/lib/icomoon2/ directory and including the icon class name here. This field is only necessary if the desired icon is not available in the fontawesome icon set."
        )
    text = RichTextField(
        blank=False,
        default="",
        verbose_name="Body Text",
        help_text="Body text to be displayed on the home page card."
        )
    card_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Card URL",
        help_text="External URL to link to from the card.  If both Card URL and Card Page are provided, Card Page will take precedence."
        )
    card_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Card Page",
        help_text="Internal page to link to from the card. If both Card Page and Card URL are provided, Card Page will take precedence.",
    )
    card_link_text = models.CharField(
        max_length=100,
        default='Learn more',
        help_text="Text displayed for the link to the related URL.  Default='Learn more'",
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('icon_name'),
        FieldPanel('icomoon_icon_name'),
        FieldPanel('text'),
        FieldPanel('card_url'),
        PageChooserPanel('card_page'),
        FieldPanel('card_link_text'),
    ]

    def clean(self):
        super().clean()
        if not self.card_page and not self.card_url:
            raise ValidationError('Either Card Page or Card URL must be set.')
        if not self.icon_name and not self.icomoon_icon_name:
            raise ValidationError('Either Icon or Icomoon Icon Name must be set.')

class TestHomePage(Page):
    """ Home page test model for development testing purposes - identical to HomePage """
    tagline = models.CharField(max_length=100, blank=False, default="")
    welcome = RichTextField(blank=False, default="")
    search_box_title = models.CharField(max_length=255, blank=False, default="",
        verbose_name="Search Box Title")
    search_box_placeholder = models.CharField(max_length=255, blank=False, default="",
        verbose_name="Search Box Placeholder")
    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Hero banner image displayed at the top of the home page.',
    )
    hero_heading_highlight = models.CharField(
        max_length=50,
        default='GDEX.',
        blank=True,
        help_text='First word shown in blue e.g. "GDEX."'
    )
    hero_heading = models.CharField(
        max_length=200,
        default='The system of record for Earth system science.',
        blank=True,
        help_text='Main heading text after the highlighted word'
    )
    hero_description = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_heading_highlight'),
            FieldPanel('hero_heading'),
            FieldPanel('hero_description'),
        ], heading='Hero Section'),
        FieldPanel('banner_image'),
        FieldPanel('tagline', classname="collapsible collapsed"),
        FieldPanel('welcome', classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel('search_box_title'),
            FieldPanel('search_box_placeholder'),
        ], heading="Search Box", classname="collapsible collapsed"),
        MultiFieldPanel([
            InlinePanel('search_suggestions', label='Search suggestion'),
        ], heading="Search suggestions", classname="collapsible collapsed"),
        MultiFieldPanel([
            InlinePanel('featured_cards', label='Featured card'),
        ], heading="Featured cards", classname="collapsible collapsed"),
    ]

class TaxonomyTerm(Orderable):
    card = ParentalKey('Card', related_name='taxonomyterm', on_delete=models.CASCADE)
    term = models.CharField(max_length=255, blank=True, default="")
    href = models.URLField(blank=True, null=True)
    panels = [
    	FieldPanel('term'),
    	FieldPanel('href')
    ]

class Card(Orderable, ClusterableModel):
    """ Card model for generic page sections """
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
        FieldPanel('image'),
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
    menu_title = models.CharField(max_length=50, blank=True, default="",
        help_text='Short title to use in the navigation bar menu.  If blank, the page title will be used.')
    intro = RichTextField(blank=True, default="")
    sidebar = models.BooleanField(default=True)
    table_of_contents = models.BooleanField(default=False)

    #page_options = StreamField([
    #    ('sidebar', BooleanBlock(required=True, help_text='Display With Sidebar')),
    #], block_counts={'sidebar':{'min_num':1,'max_num':1}},
    #   use_json_field=True,
    #   blank=False)

    content_panels = Page.content_panels + [
    #    StreamFieldPanel('page_options'),
        FieldPanel('menu_title'),
        FieldPanel('sidebar'),
        FieldPanel('table_of_contents'),
        FieldPanel('intro'),
    	InlinePanel('cards', label='Cards'),
    ]

class StaffPage(Page):
    # Database fields
    menu_title = models.CharField(max_length=50, blank=True, default="",
        help_text='Short title to use in the navigation bar menu.  If blank, the page title will be used.')
    body = RichTextField(blank=True)
    mission = RichTextField(blank=True)
    cts_text = RichTextField(blank=True)
    additional_information = RichTextField(blank=True)

    # Editor panels configuration
    content_panels = Page.content_panels + [
        FieldPanel('menu_title'),
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
    menu_title = models.CharField(max_length=50, blank=True, default="",
        help_text='Short title to use in the navigation bar menu.  If blank, the page title will be used.')

    content_panels = Page.content_panels + [
        FieldPanel('menu_title'),
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
        FieldPanel('file_name')
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
        FieldPanel('image'),
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
    menu_title = models.CharField(max_length=50, blank=True, default="",
        help_text='Short title to use in the navigation bar menu.  If blank, the page title will be used.')
    content_panels = Page.content_panels + [
        FieldPanel('menu_title'),
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
    menu_title = models.CharField(max_length=50, blank=True, default="",
        help_text='Short title to use in the navigation bar menu.  If blank, the page title will be used.')
    body = RichTextField(blank=True)
    content_panels = Page.content_panels + [
        FieldPanel('menu_title'),
        FieldPanel('body', classname='full'),
    ]

class RedirectPage(Page):
    menu_title = models.CharField(max_length=50, blank=True, default="",
        help_text='Short title to use in the navigation bar menu.  If blank, the page title will be used.')
    redirect_url = models.URLField(
        blank=False,
        null=False,
        verbose_name="Redirect URL",
    )
    content_panels = Page.content_panels + [
        FieldPanel('menu_title'),
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
