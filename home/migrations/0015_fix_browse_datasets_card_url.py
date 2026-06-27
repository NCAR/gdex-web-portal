"""
Data migration: update any "Browse Datasets" feature card that still points
to the old search page (/lookfordata/, /find-data/, etc.) to the new Globus
search page at /gsearch/dataset-search/.

The lookfordata app is no longer part of the codebase, so the card_page FK
may reference a now-orphaned Wagtail page.  Clearing card_page and setting
card_url to the new path is the clean fix.
"""
from django.db import migrations

NEW_SEARCH_URL = '/gsearch/dataset-search/'

# Slugs and URL fragments that identify old search pages
OLD_SLUGS = {'lookfordata', 'look-for-data', 'find-data', 'dataset-search-old'}
OLD_URL_FRAGMENTS = ['/lookfordata', '/find-data', '/look-for-data']


def _looks_like_old_search(card, Page):
    """Return True if this card is linked to an old search page."""
    # Check explicit URL field
    if card.card_url:
        url = card.card_url.rstrip('/')
        if any(url.endswith(frag.rstrip('/')) for frag in OLD_URL_FRAGMENTS):
            return True

    # Check linked Wagtail page slug
    if card.card_page_id:
        try:
            page = Page.objects.get(pk=card.card_page_id)
            if page.slug in OLD_SLUGS:
                return True
            # Also catch anything that resolves to /lookfordata/…
            full_url = page.url if hasattr(page, 'url') else ''
            if any(frag in full_url for frag in OLD_URL_FRAGMENTS):
                return True
        except Page.DoesNotExist:
            # Orphaned FK — treat as needing a fix if title matches
            pass

    return False


def update_browse_cards(apps, schema_editor):
    Page = apps.get_model('wagtailcore', 'Page')

    for model_name in ('TestHomePageFeaturedCard', 'FeaturedCard'):
        try:
            CardModel = apps.get_model('home', model_name)
        except LookupError:
            continue

        for card in CardModel.objects.all():
            # Match by title OR by resolving the linked URL
            title_match = 'browse' in card.title.lower() and 'dataset' in card.title.lower()
            url_match = _looks_like_old_search(card, Page)

            if title_match or url_match:
                card.card_url = NEW_SEARCH_URL
                card.card_page_id = None
                card.save()


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_testhomepagefeaturedcard_card_link_text_and_more'),
    ]

    operations = [
        migrations.RunPython(update_browse_cards, migrations.RunPython.noop),
    ]
