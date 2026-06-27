# GDEX Web Portal — SIParCS 2026 Code Changes

**Branch:** `siparcs26`  
**Base:** `main`  
**Summary:** 34 files changed, 2,873 insertions, 370 deletions  
**Purpose:** New homepage and search-page design blended into the existing Django/Wagtail codebase, running alongside the original pages.

---

## Table of Contents

1. [Overview of the Approach](#1-overview-of-the-approach)
2. [Infrastructure & Configuration](#2-infrastructure--configuration)
3. [Base Template (`base.html`)](#3-base-template-basehtml)
4. [Global Header Changes](#4-global-header-changes)
5. [Homepage — Django Model (`home/models.py`)](#5-homepage--django-model-homemodels.py)
6. [Homepage — Database Migration](#6-homepage--database-migration)
7. [Homepage — Main Template (`test_home_page.html`)](#7-homepage--main-template-test_home_pagehtml)
8. [Homepage — Search Bar & Chips (`test_home_search_bar.html`)](#8-homepage--search-bar--chips-test_home_search_barhtml)
9. [Homepage — Feature Cards (`test_home_grid_cards.html`)](#9-homepage--feature-cards-test_home_grid_cardshtml)
10. [Homepage — Popular Datasets (`test_home_popular_datasets.html`)](#10-homepage--popular-datasets-test_home_popular_datasetshtml)
11. [Homepage — Metrics (`test_home_metrics.html`)](#11-homepage--metrics-test_home_metricshtml)
12. [Homepage — CSS (`home/static/css/home_page.css`)](#12-homepage--css-homestaticcsshome_pagecss)
13. [Search Page — Main Template (`search.html`)](#13-search-page--main-template-searchhtml)
14. [Search Page — New Sidebar (`search-sidebar.html`)](#14-search-page--new-sidebar-search-sidebarhtml)
15. [Search Page — Summary (`search-summary.html`)](#15-search-page--summary-search-summaryhtml)
16. [Search Page — Result Cards (`search-results.html`)](#16-search-page--result-cards-search-resultshtml)
17. [Search Page — Base Template (`search-base.html`)](#17-search-page--base-template-search-basehtml)
18. [Search Page — JavaScript (`search_data.js`)](#18-search-page--javascript-search_datajs)
19. [Search Page — CSS (`search_data.css`)](#19-search-page--css-search_datacss)
20. [Globus Search — Field Extractors (`globus_search_fields.py`)](#20-globus-search--field-extractors-globus_search_fieldspy)
21. [Globus Search — Index Registration (`globus_search_indexes.py`)](#21-globus-search--index-registration-globus_search_indexespy)
22. [Template Tag: `has_active_bucket`](#22-template-tag-has_active_bucket)
23. [Static Assets Added](#23-static-assets-added)
24. [Removed / Cleaned Up Code](#24-removed--cleaned-up-code)
25. [Files NOT Changed (Original Pages)](#25-files-not-changed-original-pages)
26. [Commit History (Meaningful Commits Only)](#26-commit-history-meaningful-commits-only)
27. [Location Cascade Filter](#27-location-cascade-filter-search-sidebarhtml-search_datajs)
28. [Selected Filters Chip System](#28-selected-filters-chip-system-searchhtml-search_datajs-gsearchviewspy)
29. [Temporal Preset Improvements](#29-temporal-preset-improvements-gsearchviewspy-searchhtml-search-sidebarhtml)
30. [Browse Datasets Card URL Fix](#30-browse-datasets-card-url-fix-hometemplateshometest_home_grid_cardshtml-homemigrations)
31. [Non-Scrollable Filter Sidebar](#31-non-scrollable-filter-sidebar-search_datacss-search_datajs-search-sidebarhtml)
32. [Homepage Hero & Chip Polish](#32-homepage-hero--chip-polish-homestaticcsshome_pagecss-test_home_search_barhtml)
33. [Ancillary Dataset Badge](#33-ancillary-dataset-badge-search-resultshtml-search_datacss)
34. [Specialized Dataset Pages — AI-Ready & Popular](#34-specialized-dataset-pages--ai-ready--popular-gsearch)
35. [Pagination Redesign](#35-pagination-redesign-search-paginationhtml-search_datacss)
36. [Hero Heading GDEX Color](#36-hero-heading-gdex-color-homestaticcsshome_pagecss)
37. [Specialized Pages — Spacing & Navigation](#37-specialized-pages--spacing--navigation-ai-ready-datasetshtml-popular-datasetshtml)
38. [Custom Temporal Range — Apply Button & Reset Fix](#38-custom-temporal-range--apply-button--reset-fix-search-sidebarhtml-searchhtml-search_datacss)

---

## 1. Overview of the Approach

The new design runs **in parallel with the original** — nothing in `main` was broken or replaced. Two page types coexist:

| | Original | New Design |
|---|---|---|
| Wagtail model | `HomePage` | `TestHomePage` |
| Main template | `home/templates/home/home_page.html` | `home/templates/home/test_home_page.html` |
| URL (example) | `/` | `/gdex-test-home-page/` |

The header logo link was pointed to `/gdex-test-home-page/` so the test design is what you see when you navigate normally on the test instance, but the original `HomePage` model and template are untouched.

The design system is **NCAR Unity** (Bootstrap-based), loaded globally via `base.html`. All new page-specific styles use BEM-style `.gdex-*` class names in dedicated CSS files, keeping them isolated from the global Unity styles.

---

## 2. Infrastructure & Configuration

### `.gitignore`
**File:** `.gitignore`

```diff
+ # New search page design (work in progress, not ready for codebase)
+ gsearch/search/
```

Added an ignore entry for `gsearch/search/` — a work-in-progress directory that was not ready to be committed.

### CI / Helm chart
**Files:** `app-chart/values.yaml`, `app-chart/values.yaml.siparcs26`, `app-chart/values.yaml.tcram`

The CI pipeline (`siparcs26` GitHub Actions workflow) automatically bumps the container image tag in `values.yaml.siparcs26` on every successful build. No manual changes needed here — these are machine-written commits.

The workflow trigger was also updated:
```diff
# .github/workflows/...
- branches: [siparcs26]
+ branches: [siparcs26/**]   # matches siparcs26 and any sub-branches
```

---

## 3. Base Template (`base.html`)

**File:** `gdexwebserver/templates/base.html`  
**What changed:** Two targeted additions to unlock page-level customization.

### Before
```html
<main class="container-lg py-3 pt-md-4">
    {% include "unity/breadcrumbs.html" %}
    {% block content %}{% endblock %}
</main>
...
<script src="{% static 'unity/js/main.min.js' %}"></script>
```

### After
```html
<main class="{% block main_class %}container-lg py-3 pt-md-4{% endblock %}">
    {% block breadcrumbs %}{% include "unity/breadcrumbs.html" %}{% endblock %}
    {% block content %}{% endblock %}
</main>
...
<script src="{% static 'unity/js/main.min.js' %}"></script>
{% block extra_js %}{% endblock %}
```

**Why each change matters:**

| Change | Purpose |
|---|---|
| `{% block main_class %}` | The search page hero must span 100% viewport width. By exposing this block, `search.html` can pass `p-0` to remove the default `container-lg` padding. The default string keeps all other pages unaffected. |
| `{% block breadcrumbs %}` | The hero sections on both the home page and search page provide page context, making the breadcrumb trail redundant and visually conflicting. Each page can suppress breadcrumbs without modifying global code. |
| `{% block extra_js %}` | Gives each page a safe place to load page-specific JavaScript after Bootstrap loads but before `</html>`. Used by the search page to load `search_data.js`. |

---

## 4. Global Header Changes

### `header_ncar_logo.html`
**File:** `gdexwebserver/templates/unity/header_ncar_logo.html`

```diff
- <a href="/">
+ <a href="/gdex-test-home-page/">
    {% include "unity/picture_wagtail_media.html" with image="logo-ncar-2026" alt="NSF NCAR" %}
  </a>
  ...
- <a href="/">Geoscience Data Exchange (GDEX)</a>
+ <a href="/gdex-test-home-page/">Geoscience Data Exchange (GDEX)</a>
```

Both the NCAR logo and the site-name link now point to `/gdex-test-home-page/` instead of `/`. This makes the new design the "home" destination for the test instance. **The original `HomePage` at `/` is still live** — these links are just redirecting users to the test page during development.

### `header_decs.html`
**File:** `gdexwebserver/templates/unity/header_decs.html`

```diff
- {% if request.get_host|slice:"0:4" != "gdex" ... %}
-   <div class="alert alert-warning text-center mb-0 fw-bold sticky-top" ...>
-       TEST INSTANCE - {{ request.get_host }}
-   </div>
- {% endif %}
- 
- <header>
+ <header>
+   {% if request.get_host|slice:"0:4" != "gdex" ... %}
+   <div style="background:#cc0000;color:#fff;font-size:0.75rem;...">
+       TEST INSTANCE — {{ request.get_host }}
+   </div>
+   {% endif %}
```

The "TEST INSTANCE" banner was:
1. Moved **inside** `<header>` (was above it, causing z-index conflicts with the hero's sticky header)
2. Restyled from a Bootstrap `alert-warning` block to a compact red bar (less visually disruptive)
3. Logic preserved — only shows on non-`gdex.*` hostnames

---

## 5. Homepage — Django Model (`home/models.py`)

**File:** `home/models.py`  
**What changed:** Three new fields added to the existing `TestHomePage` model. The `HomePage` model was untouched.

### New fields on `TestHomePage`

```python
# Added to TestHomePage (line ~429)
banner_image = models.ForeignKey(
    'wagtailimages.Image',
    null=True, blank=True,
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
```

And in `content_panels`:
```python
MultiFieldPanel([
    FieldPanel('hero_heading_highlight'),
    FieldPanel('hero_heading'),
    FieldPanel('hero_description'),
], heading='Hero Section'),
FieldPanel('banner_image'),
```

**Effect:** Wagtail CMS editors can now:
- Upload a custom hero background image (falls back to `hero_earth.png` if blank)
- Edit the hero heading with a separately highlighted prefix word (shown in blue)
- Write the hero description as rich text

These are all optional — the template has sensible defaults if they are left blank.

Also note: `TestHomePageSearchSuggestion` gained an optional `description` field (shown under chips), and `TestHomePageFeaturedCard` gained `card_link_text` (the "Learn more →" label is now editable per card).

---

## 6. Homepage — Database Migration

**File:** `home/migrations/0011_homepage_banner_image_alter_alertmessage_end_date_and_more.py`

Auto-generated Django migration that adds the `banner_image` FK to `HomePage` (note: the migration name says `homepage` but the field was also added to `TestHomePage` in an earlier migration). Also adjusts `AlertMessage.start_date` and `AlertMessage.end_date` default values to the current date at migration time.

**Team note:** Run `python manage.py migrate home` on the test instance to apply.

---

## 7. Homepage — Main Template (`test_home_page.html`)

**File:** `home/templates/home/test_home_page.html`

This is the shell that composes the entire new homepage. It was almost completely rewritten.

### Before (original `test_home_page.html`)
```html
{% extends "base.html" %}
{% load wagtailcore_tags %}

{% block content %}
<div class="d-grid d-print-flex">
    <article class="main-content-wrapper">
        {% block welcome_message %}
        <div class="row justify-content-center">
            <div class="col-lg-10">
                <div class="text-center">
                    <h3 class="display-6 text-black mb-2">{{ page.tagline|richtext }}</h3>
                    <p class="text-black-50">{{ page.welcome|richtext }}</p>
                </div>
            </div>
        </div>
        {% endblock %}

        {% block home_search_bar %}
        {% include 'home/test_home_search_bar.html' %}
        {% endblock %}

        {% block grid_cards %}
        {% include 'home/test_home_grid_cards.html' %}
        {% endblock %}
    </article>
</div>
{% endblock %}
```

**What this was:** A plain Bootstrap article container with tagline text, old search bar, and old grid cards. No hero, no CSS, no Swiper.

### After (new `test_home_page.html`)
```html
{% extends "base.html" %}
{% load static wagtailcore_tags wagtailimages_tags %}

{% block headextras %}
<link rel="stylesheet" href="{% static 'css/home_page.css' %}">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css">
<script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
{% endblock %}

{% block breadcrumbs %}{% endblock %}

{% block content %}

<!-- HERO -->
{% static "img/hero_earth.png" as hero_fallback_img %}
{% if page.banner_image %}
    {% image page.banner_image original as hero_img %}
    <section class="gdex-hero" style="background-image: url('{{ hero_img.url }}');">
{% else %}
    <section class="gdex-hero" style="background-image: url('{{ hero_fallback_img }}');">
{% endif %}
    <div class="gdex-hero__overlay"></div>
    <div class="gdex-hero__content position-relative">
        <div class="row">
            <div class="col-lg-5 col-xl-4">
                <h1 class="gdex-hero__heading">
                    {% if page.hero_heading_highlight %}
                        <span class="gdex-hero__heading-highlight">{{ page.hero_heading_highlight }}</span>
                    {% endif %}
                    {{ page.hero_heading|default:"The system of record for Earth system science." }}
                </h1>
                <div class="gdex-hero__description">
                    {% if page.hero_description %}
                        {{ page.hero_description|richtext }}
                    {% else %}
                        <p><strong>GDEX</strong> is NSF NCAR's trusted platform...</p>
                    {% endif %}
                </div>
                <div class="gdex-hero__actions">
                    <a href="/gsearch/dataset-search/" class="gdex-hero__btn gdex-hero__btn--primary">
                        <i class="fas fa-search"></i> Browse Datasets
                    </a>
                </div>
            </div>
        </div>
    </div>
</section>

{% block home_search_bar %}
{% include 'home/test_home_search_bar.html' %}
{% endblock %}

<div class="gdex-waves-wrapper">
<img src="{% static 'unity/img/UCAR-Waves-Lines-Only.png' %}" alt="" aria-hidden="true" class="gdex-waves-img">

{% block grid_cards %}
{% include 'home/test_home_grid_cards.html' %}
{% endblock %}

{% block popular_datasets %}
{% include 'home/test_home_popular_datasets.html' %}
{% endblock %}

{% block metrics %}
{% include 'home/test_home_metrics.html' %}
{% endblock %}

</div><!-- end gdex-waves-wrapper -->

{% endblock %}
```

**Key structural decisions:**

| Decision | Why |
|---|---|
| `{% block headextras %}` loads `home_page.css` + Swiper CDN | Keeps page-specific assets out of `base.html` so other pages are unaffected |
| `{% block breadcrumbs %}{% endblock %}` (empty) | Removes the Unity breadcrumb trail — the hero serves as page context |
| Hero uses `{% image page.banner_image original %}` with fallback | Wagtail image tag processes the uploaded image; `hero_earth.png` is the default |
| `gdex-hero__heading-highlight` wraps only the first word | Creates the blue "GDEX." prefix effect via CSS color |
| `gdex-waves-wrapper` wraps sections 3–5 | The UCAR decorative wave image (`UCAR-Waves-Lines-Only.png`) is positioned absolutely inside this wrapper and spans the full height of all three sections |
| Two new blocks: `popular_datasets` and `metrics` | Allows child templates to override individual sections independently |
| Swiper loaded via CDN in `headextras` | Required by `test_home_popular_datasets.html` before the JS runs |

---

## 8. Homepage — Search Bar & Chips (`test_home_search_bar.html`)

**File:** `home/templates/home/test_home_search_bar.html`

### Before
```html
<div class="component featured-work container-lg">
    <div class="row gx-0 pt-md-4 justify-content-center">
        <div class="col-8 primary text-center">
            <div class="card">
                <div class="card-body">
                    <h3 class="card-title mb-md-2">{{ page.search_box_title }}</h3>
                    <form id="search-form" class="d-flex" name="search_form" action="/gsearch/dataset-search/">
                        <input class="form-control" type="search" id="search-input" autocomplete="off"
                               data-provide="typeahead" name="q"
                               placeholder="{{ page.search_box_placeholder }}" value="">
                        <button class="btn btn-primary" type="submit"><i class="fas fa-search"></i></button>
                    </form>
                    {% if page.search_suggestions.all %}
                    <div id="search-suggestions" class="mt-2">
                        {% for suggestion in page.search_suggestions.all %}
                        <a href="{{ suggestion.search_term_url }}">
                            <span class="badge home-search-badge rounded">{{ suggestion.search_term }}</span>
                        </a>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
```

**What this was:** A Bootstrap card, centered at `col-8`, with a standard form-control input, default badges from the CMS.

### After
```html
<!-- SEARCH OUTER — negative margin overlaps the hero -->
<div class="gdex-search-outer">
    <div class="container-lg">
        <div class="row justify-content-center">
            <div class="col-12">
                <div class="gdex-search-block">
                    <h2 class="gdex-search-block__title">
                        {{ page.search_box_title|default:"Search For Datasets" }}
                    </h2>
                    <form action="/gsearch/dataset-search/" method="get" id="gdex-home-search-form">
                        <div class="gdex-search-bar">
                            <input type="text" name="q" id="gdex-home-search-input"
                                   class="gdex-search-bar__input"
                                   placeholder="{{ page.search_box_placeholder|default:'Search by keyword or dataset number' }}"
                                   aria-label="Search datasets">
                            <button type="submit" class="gdex-search-bar__btn" aria-label="Search">
                                <i class="fas fa-search"></i>
                                <span>Search</span>
                            </button>
                        </div>
                    </form>
                    <script>
                        // Prevent submitting empty search
                        document.getElementById('gdex-home-search-form').addEventListener('submit', function (e) {
                            if (!document.getElementById('gdex-home-search-input').value.trim()) {
                                e.preventDefault();
                            }
                        });
                        // Clear input on back-navigation (browser cache restores old value)
                        if ('scrollRestoration' in history) { history.scrollRestoration = 'manual'; }
                        window.addEventListener('pageshow', function () {
                            document.getElementById('gdex-home-search-input').value = '';
                            window.scrollTo(0, 0);
                        });
                    </script>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- CHIPS -->
<div class="gdex-search-chips">
    <div class="container-lg">
        <p class="gdex-search-chips__label">Explore specialized datasets</p>
        <div class="d-flex flex-wrap gap-3 justify-content-center">
            <a href="https://gdex.ucar.edu/metrics/by-the-numbers/" ... class="gdex-chip">
                <i class="fas fa-robot me-2"></i>
                <span>
                    <strong>AI-ready datasets</strong>
                    <small class="d-block">Dataset prepared for AI/ML Workflow</small>
                </span>
            </a>
            <a href="/gsearch/dataset-search/?format=zarr" class="gdex-chip">
                <i class="fas fa-layer-group me-2"></i>
                <span>
                    <strong>Zarr datasets</strong>
                    <small class="d-block">Cloud-optimized array data</small>
                </span>
            </a>
        </div>
    </div>
</div>
```

**Key changes:**

| Change | Before | After |
|---|---|---|
| Layout | Bootstrap card, col-8, centered | Full-width `gdex-search-outer` with negative margin overlapping hero |
| Visual overlap | No overlap with hero | `margin-top: -6rem` creates a floating-over-hero effect |
| Input width | col-8 (narrow) | col-12 (full width within container) |
| Submit guard | None | JS blocks empty submits |
| Back-nav fix | None | `pageshow` clears input and scrolls to top (browser restores cached values otherwise) |
| Suggestions | CMS-driven badges from `search_suggestions` | Hardcoded chips (AI-ready, Zarr) with icons and descriptions |
| Method | `data-provide="typeahead"` (old jQuery) | Plain `method="get"` |

---

## 9. Homepage — Feature Cards (`test_home_grid_cards.html`)

**File:** `home/templates/home/test_home_grid_cards.html`

### Before
```html
{% load wagtailcore_tags %}
<div class="component featured-work container-lg pt-md-4">
    <div class="row gx-0 justify-content-center">
        <div class="col-10 primary">
            <div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 g-2 g-md-4">
                {% for card in page.featured_cards.all %}
                <div class="col">
                    <div class="card h-100 grid-card-group">
                        <a href="..." class="stretched-link" ...></a>
                        <div class="card-body">
                            <div class="icon py-2 text-center">
                                {% if card.icon_name %}
                                <i class="fa-solid fa-{{ card.icon_name }} fa-2x"></i>
                                {% elif card.icomoon_icon_name %}
                                <i class="{{ card.icomoon_icon_name }}" style="font-size: 3em;"></i>
                                {% endif %}
                            </div>
                            <h4 class="card-title text-center text-white">{{ card.title }}...</h4>
                            <div class="card-text text-center pt-2">{{ card.text|richtext }}</div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
```

**What this was:** Dark Bootstrap cards with white text, icon at top, title, body. Icon inline-styled at `font-size: 3em`. The link was a `stretched-link` on an invisible `<a>` inside the card.

### After
```html
{% load static wagtailcore_tags %}
<!-- FEATURE CARDS -->
<section class="gdex-features-section">
    <div class="container-lg">
        <h2 class="gdex-section-title">What You Can Do With GDEX</h2>
        <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
            {% for card in page.featured_cards.all %}
            <div class="col">
                <div class="gdex-feature-card">
                    <div class="gdex-feature-card__icon">
                        {% if card.icon_name %}
                            <i class="fa-solid fa-{{ card.icon_name }}"></i>
                        {% elif card.icomoon_icon_name %}
                            <i class="{{ card.icomoon_icon_name }}"></i>
                        {% endif %}
                    </div>
                    <h3 class="gdex-feature-card__title">{{ card.title }}</h3>
                    <div class="gdex-feature-card__desc">{{ card.text|richtext }}</div>
                    <a href="{% if card.card_page %}{{ card.card_page.url }}{% else %}{{ card.card_url }}{% endif %}"
                       class="gdex-feature-card__link stretched-link"
                       {% if not card.card_page and card.card_url %}target="_blank" rel="noopener noreferrer"{% endif %}>
                        {{ card.card_link_text }} &rarr;
                    </a>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</section>
```

**Key changes:**

| Change | Before | After |
|---|---|---|
| Section heading | None | "What You Can Do With GDEX" (`.gdex-section-title`) |
| Card visual | Dark Bootstrap card, white text | Light `.gdex-feature-card` with gradient border, hover lift |
| Icon | Inline-styled large icon | Icon in 60×60 blue rounded square (`.gdex-feature-card__icon`) |
| Icon size control | `fa-2x` or `style="font-size:3em"` | Controlled by CSS `.gdex-feature-card__icon i { font-size: 1.45rem }` |
| Link label | None (invisible stretched-link) | `{{ card.card_link_text }} →` — now CMS-editable per card |
| Container | `col-10` (narrower) | `container-lg` (full container) |
| Background | Unity default (grey/dark) | `.gdex-features-section { background-color: #f2f2f2 }` |

---

## 10. Homepage — Popular Datasets (`test_home_popular_datasets.html`)

**File:** `home/templates/home/test_home_popular_datasets.html`  
**Status:** New file (did not exist on `main`)

This entire template is new. It creates the "Explore Popular Datasets" carousel.

```html
{% load static wagtailcore_tags %}

<section class="gdex-popular-section">
    <div class="container-lg">
        <div class="d-flex align-items-center justify-content-between mb-2">
            <h2 class="gdex-section-title mb-0">Explore Popular Datasets</h2>
            <a href="https://gdex.ucar.edu/metrics/by-the-numbers/" ... class="gdex-popular-section__view-all">
                View all datasets &rarr;
            </a>
        </div>

        <div class="gdex-datasets-swiper-wrapper">
            <div class="swiper gdex-datasets-swiper">
                <div class="swiper-wrapper" id="gdex-popular-datasets-wrapper">
                    <!-- slides injected by JS after API call -->
                </div>
            </div>
            <div class="gdex-swiper-prev"><i class="fas fa-chevron-left"></i></div>
            <div class="gdex-swiper-next"><i class="fas fa-chevron-right"></i></div>
        </div>
    </div>
</section>

<script>
(function () {
    var placeholderImgs = [
        '{% static "img/hero_earth.png" %}',
        '{% static "img/20cr_v3.png" %}'
    ];
    var apiUrl = '{% url "top_datasets" %}';

    function fmt(n) { return Number(n).toLocaleString(); }
    function fmtVol(tb) {
        var n = parseFloat(tb);
        return n >= 1000 ? (n / 1000).toFixed(1) + ' PB' : Math.round(n) + ' TB';
    }

    fetch(apiUrl)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var wrapper = document.getElementById('gdex-popular-datasets-wrapper');
            data.top_datasets.forEach(function (ds, i) {
                var img = placeholderImgs[i % placeholderImgs.length];
                var slide = document.createElement('div');
                slide.className = 'swiper-slide';
                slide.innerHTML =
                    '<a href="/datasets/' + ds.dataset + '" class="gdex-dataset-card">' +
                        '<div class="gdex-dataset-card__circle">' +
                            '<img src="' + img + '" alt="' + ds.OName + '">' +
                        '</div>' +
                        '<div class="gdex-dataset-card__body">' +
                            '<div class="gdex-dataset-card__size">#' + ds.index + '</div>' +
                            '<h4 class="gdex-dataset-card__name">' + ds.OName + '</h4>' +
                            '<div class="gdex-dataset-card__meta">' +
                                '<span class="gdex-dataset-card__badge">' + fmt(ds['Total Number of Unique Users']) + ' users</span>' +
                                '<span class="gdex-dataset-card__badge">' + fmtVol(ds['Total Volume Downloaded (TB)']) + ' downloaded</span>' +
                            '</div>' +
                        '</div>' +
                    '</a>';
                wrapper.appendChild(slide);
            });

            new Swiper('.gdex-datasets-swiper', {
                slidesPerView: 1,
                spaceBetween: 24,
                loop: true,
                autoplay: { delay: 5000, disableOnInteraction: false, pauseOnMouseEnter: true },
                navigation: { prevEl: '.gdex-swiper-prev', nextEl: '.gdex-swiper-next' },
                breakpoints: {
                    640:  { slidesPerView: 1 },
                    768:  { slidesPerView: 1 },
                    1024: { slidesPerView: 2 },
                    1400: { slidesPerView: 3 },
                }
            });
        })
        .catch(function () {
            // Hide the swiper wrapper silently if the API is unavailable
            document.getElementById('gdex-popular-datasets-wrapper')
                .closest('.gdex-datasets-swiper-wrapper').style.display = 'none';
        });
}());
</script>
```

**How it works:**
1. On page load, JS fetches `/api/metrics/top_datasets/` (existing GDEX API endpoint)
2. For each dataset returned, a `swiper-slide` is created with: circular image (alternating between 2 placeholder images), rank number, dataset name, user count badge, download volume badge
3. Swiper.js is initialized with: autoplay (5 s), loop, custom prev/next buttons, responsive `slidesPerView` (1 → 2 → 3)
4. On API failure: the wrapper is hidden cleanly (no error shown to users)

---

## 11. Homepage — Metrics (`test_home_metrics.html`)

**File:** `home/templates/home/test_home_metrics.html`  
**Status:** New file (did not exist on `main`)

```html
{% load static %}
{% static 'img/hero_earth.png' as metrics_bg %}

<section class="gdex-metrics-section" style="background-image: url('{{ metrics_bg }}');">
    <div class="container-lg">
        <h2 class="gdex-metrics-section__title">GDEX By the Metrics</h2>
        <div class="row row-cols-2 row-cols-md-3 row-cols-lg-6 g-4">
            <div class="col">
                <div class="gdex-metric">
                    <div class="gdex-metric__icon"><i class="icon-data-software-services"></i></div>
                    <div class="gdex-metric__value" id="gdex-metric-datasets">&hellip;</div>
                    <div class="gdex-metric__label">Total Datasets</div>
                </div>
            </div>
            <!-- ... 5 more metric cards ... -->
        </div>
    </div>
</section>

<script>
(function () {
    function fmt(n) { return Number(n).toLocaleString(); }

    function countUp(el, target, suffix, isFloat) {
        var duration = 1800;
        var startTime = null;
        suffix = suffix || '';
        function step(ts) {
            if (!startTime) startTime = ts;
            var progress = Math.min((ts - startTime) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);   // cubic ease-out
            var current = target * eased;
            el.textContent = isFloat
                ? current.toFixed(2) + suffix
                : fmt(Math.floor(current)) + suffix;
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    var metrics = [
        { url: '{% url "total_datasets" %}',    id: 'gdex-metric-datasets',  get: function (d) { return d.value; } },
        { url: '{% url "total_citations" %}',   id: 'gdex-metric-citations', get: function (d) { return d.value; } },
        { url: '{% url "unique_users" %}',      id: 'gdex-metric-users',     get: function (d) { return d.ips; } },
        { url: '{% url "volume_downloaded" %}', id: 'gdex-metric-downloaded',get: function (d) { return d.volume; }, suffix: ' PB', float: true },
        { url: '{% url "gdex_volume" %}',       id: 'gdex-metric-volume',    get: function (d) { return d.value; }, suffix: ' PB', float: true },
        { url: '{% url "total_requests" %}',    id: 'gdex-metric-requests',  get: function (d) { return d.value; } },
    ];

    function runAll() {
        metrics.forEach(function (m) {
            fetch(m.url)
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    var el = document.getElementById(m.id);
                    if (!el) return;
                    var target = parseFloat(m.get(data));
                    if (isNaN(target)) { el.textContent = '—'; return; }
                    countUp(el, target, m.suffix, m.float);
                })
                .catch(function () {
                    var el = document.getElementById(m.id);
                    if (el) el.textContent = '—';
                });
        });
    }

    // Fire when section scrolls into view (IntersectionObserver, fallback to immediate)
    var section = document.querySelector('.gdex-metrics-section');
    if ('IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function (entries) {
            if (entries[0].isIntersecting) {
                observer.unobserve(section);
                runAll();
            }
        }, { threshold: 0.15 });
        observer.observe(section);
    } else {
        runAll();
    }
}());
</script>
```

**The 6 metrics and their API endpoints:**

| Card | API URL name | Response key | Notes |
|---|---|---|---|
| Total Datasets | `total_datasets` | `d.value` | Integer |
| Total Citations | `total_citations` | `d.value` | Integer |
| Unique IPs | `unique_users` | `d.ips` | Integer |
| Data Downloaded | `volume_downloaded` | `d.volume` | Float, suffix ` PB` |
| Size of GDEX | `gdex_volume` | `d.value` | Float, suffix ` PB` |
| Customized Requests | `total_requests` | `d.value` | Integer |

**Animation:** Cubic ease-out count-up over 1800 ms, fires on `IntersectionObserver` at 15% visibility. Falls back to immediate on browsers without `IntersectionObserver`. On fetch error, shows `—` instead of crashing.

---

## 12. Homepage — CSS (`home/static/css/home_page.css`)

**File:** `home/static/css/home_page.css`  
**Status:** New file (578 lines)

This file is loaded only on `test_home_page.html`. It contains all visual styling for the new homepage. Here is what each section covers:

### Layout resets (lines 1–7)
```css
body { overflow-x: hidden; }
main:has(.gdex-hero) { padding-top: 0 !important; }
main:has(.gdex-metrics-section) { padding-bottom: 0 !important; }
```
Removes Unity's default `py-3 pt-md-4` padding when the hero or metrics section is present, so both can reach the viewport edge.

### Shared section titles (lines 9–22)
`.gdex-section-title` and `.gdex-section-subtitle` — Poppins 700, dark navy, `clamp()` sizing for fluid type.

### UCAR Waves (lines 25–44)
`.gdex-waves-wrapper` — breaks out of container with `width: 100vw; margin-left: calc(-50vw + 50%)`. The wave PNG is `position: absolute`, right-aligned, 38% wide, 22% opacity, `z-index: 10`, behind the cards but in front of backgrounds.

### Hero (lines 47–149)
Complete BEM block for `.gdex-hero`. Key values:
- `min-height: 540px`, `background-size: cover`, `background-position: center right`
- Overlay: `rgba(0,0,0,0.50)` semi-transparent black
- Heading: Poppins 700, `clamp(1.6rem, 3.2vw, 2.5rem)`, white, `text-shadow`
- Highlight color: `#2952c4` (GDEX blue)
- Primary button: `#2952c4` bg, hover darkens + `translateY(-2px)` lift
- Outline button: transparent, white border (for a potential secondary CTA)

### Search outer + search block (lines 152–224)
`.gdex-search-outer`:
- `margin-top: -6rem` — creates the hero overlap
- `z-index: 10` — floats above hero
- `::after` pseudo-element fills white background below the blue search block

`.gdex-search-block`: blue (#2952c4) padding block, `box-shadow`.

`.gdex-search-bar__btn`: amber/gold (#f59e0b) with navy text — high contrast CTA.

### Chips (lines 227–271)
`.gdex-chip`: white card, 295px min-width, blue border, hover inverts to blue background with white text.

### Feature cards (lines 274–354)
`.gdex-feature-card`: light grey background, 25px border-radius, gradient border via `::before` pseudo-element mask technique, hover `translateY(-6px)` lift.

The gradient border trick uses:
```css
.gdex-feature-card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 25px;
    padding: 4px;
    background: linear-gradient(to top right, rgba(41,82,196,0.35), rgba(41,82,196,1.00));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
}
```
This draws only the border area — content area is cut out using mask compositing.

### Popular datasets (lines 357–487)
- `.gdex-popular-section`: white background section
- `.gdex-datasets-swiper-wrapper`: `padding: 0 3rem` to make room for arrow buttons
- `.gdex-swiper-prev/next`: circular white buttons, blue on hover, positioned at `top: 50%`
- `.gdex-dataset-card`: horizontal row layout (circle image + text body)
- `.gdex-dataset-card__circle`: 140×140px circle with blue border and box-shadow
- `.gdex-dataset-card__badge`: small uppercase blue-on-light-blue badges

### Metrics (lines 490–551)
- `.gdex-metrics-section`: dark navy `#0d1f5c` background, `background-attachment: fixed` (parallax), `background-size: cover`
- `.gdex-metric`: white rounded card with hover lift
- `.gdex-metric__icon`: 54px blue circle
- `.gdex-metric__value`: Poppins 700, dark navy, `clamp()` sizing
- `.gdex-metric__label`: tiny uppercase grey label

### Mobile breakpoints (lines 554–578)
```css
@media (max-width: 767px) {
    .gdex-hero { min-height: 320px; padding-bottom: 4rem; }
    .gdex-search-block { padding: 1.5rem 0; }
    .gdex-search-bar { flex-direction: column; gap: 0.5rem; }
    .gdex-dataset-card__circle { width: 80px; height: 80px; min-width: 80px; }
    .gdex-waves-img { display: none; }
    /* etc. */
}
```
Search bar stacks vertically on mobile. Circle images shrink. Wave decoration hides on small screens.

---

## 13. Search Page — Main Template (`search.html`)

**File:** `gsearch/templates/gsearch/dataset-search/globus-portal-framework/search.html`

### Before
```html
{% extends 'gsearch/dataset-search/globus-portal-framework/search-base.html' %}
{% load static index_template is_active %}

{% block body %}
  <h1 class="h1 border-bottom">Search GDEX</h1>
  <div class="lead mb-3">Search and discover datasets...</div>
  <div class="mb-3 fst-italic">GDEX search powered by Globus Search...</div>

  {% block search_nav %}...{% endblock %}

  <div class="tab-content" id="search-nav-tabContent">
    <div class="tab-pane fade show active ...">
      <form id="search-form" class="my-4 d-flex" ...>
        <input class="form-control" type="text" id="search-input" ...>
        <button id="search-btn" type="submit" class="btn btn-primary">
          <i class="fas fa-search"></i>
        </button>
      </form>

      <div class="row">
        <!-- sidebar: col-sm-4 -->
        <!-- content: col-sm-8 -->
      </div>
    </div>

    <div class="tab-pane fade ...">
      <!-- About tab -->
    </div>
  </div>
{% endblock %}
```

**What this was:** Plain Bootstrap layout. A `<h1>` heading, lead paragraph, tab navigation (Search/About), standard Bootstrap row with sidebar and content columns. Search form used old `data-provide="typeahead"`.

### After
See [Section 13 template above](#13-search-page--main-template-searchhtml) — complete rewrite. Key structural changes:

| Change | Before | After |
|---|---|---|
| Page heading | `<h1 class="h1 border-bottom">Search GDEX</h1>` | Full-width hero section with background image |
| Search form | Inside content area | Inside hero, styled as `.gdex-find-data-hero__form` |
| Layout | Bootstrap row with `col-sm-4` / `col-sm-8` | CSS Grid `.gdex-find-data-layout` with sidebar + results area |
| Tabs | Search tab + About tab | No tabs (About removed) |
| Sidebar | `components/search-filters.html` + `components/search-facets.html` | New `components/search-sidebar.html` (single unified component) |
| Filter chips | Shown inside `search-summary.html` | Shown in dedicated `.gdex-results-filters-row` bar |
| Reset button | None | `.gdex-btn-reset` ("Reset Search") |
| Active filter removal | `removeFilter()` inline JS | `gdexRemoveFilter()` helper defined in `search.html` |
| Breadcrumbs | Visible | Hidden (`{% block breadcrumbs %}{% endblock %}`) |
| Main container | Unity default `container-lg py-3 pt-md-4` | `p-0` (hero spans full width) |
| Extra JS | None | `search_data.js` loaded via `{% block extra_js %}` |
| UCAR waves | None | CSS custom property `--waves-url` on `.gdex-find-data-body` |
| `gsearch_tags` | Not loaded | `{% load ... gsearch_tags %}` (needed for `truncate_facet`, `has_active_bucket`) |

---

## 14. Search Page — New Sidebar (`search-sidebar.html`)

**File:** `gsearch/templates/gsearch/dataset-search/globus-portal-framework/components/search-sidebar.html`  
**Status:** New file (112 lines — replaces the old `search-filters.html` + `search-facets.html` pair)

The sidebar consolidates what used to be two separate form components into one `<aside>`. Structure:

```
<aside class="gdex-filters-sidebar">
  ├── Header ("Filters" title + "clear all" link)
  └── .gdex-filters-sidebar__scroll-body
       ├── Time Range group (always expanded)
       │   ├── 4 preset radio buttons (1/5/10/25 years)
       │   └── Custom date range inputs (id="temporal_start_input", id="temporal_end_input")
       └── For each Globus facet with buckets:
            └── .gdex-filter-group (collapsed if no active selection)
                 ├── Toggle header (facet name + chevron)
                 ├── "Search [facet]" text input (client-side filter)
                 ├── Checkboxes for each bucket (with count badge)
                 └── "see more..." button
```

**Important technical notes:**
- `temporal_start_input` / `temporal_end_input` IDs are preserved from the original code — `gsearch.js` reads these IDs
- Facet groups auto-expand if `facet|has_active_bucket` is true (uses the new `has_active_bucket` template tag)
- The "see more..." button is a hook for JS to show/hide additional options
- `onchange="customSearch(1);"` calls the existing `customSearch()` function from `gsearch.js`

---

## 15. Search Page — Summary (`search-summary.html`)

**File:** `gsearch/templates/gsearch/dataset-search/globus-portal-framework/components/search-summary.html`

### Before (64 lines)
```html
<div class="m-3" id="search-summary">
    {% block search_summary %}
    <h4 class="h4">
        {% if request.session.search.query != '*' ... %}
            You searched for '{{request.session.search.query}}'.
        {% endif %}
        {% if search.total and search.total > 0 %}
            {% if request.session.search.filters ... %}
                {{search.total}} matching dataset{{...}} found with applied filters.
            {% elif ... %}
                {{search.total}} matching dataset{{...}} found.
            {% endif %}
        {% else %}
            <span class="text-warning">No matching datasets found.</span>
        {% endif %}
    </h4>
    <!-- Applied filters display with per-filter remove badges -->
    {% if request.session.search.filters ... %}
        Applied filters: [complex badge loop with removeFilter() calls]
    {% endif %}
    {% endblock %}
</div>
```

**What this was:** A verbose `<h4>` block with complex conditional text and inline filter badges with remove buttons. Used `request.session.search.filters` (internal Globus session state).

### After (14 lines)
```html
{% block search_summary %}
{% if search.total is not None %}
<p class="gdex-results-count">
  {% if search.total > 0 %}
    {{ search.total }} dataset{{ search.total|pluralize }} found
    {% if request.session.search.query and request.session.search.query != '*' %}
      for &ldquo;{{ request.session.search.query }}&rdquo;
    {% endif %}
  {% else %}
    No matching datasets found.
  {% endif %}
</p>
{% endif %}
{% endblock %}
```

**What changed:** The active filter display was removed from here and moved to `search.html` as the `.gdex-results-filters-row` — a dedicated bar rendered from the live `search.facets` data (not the session). The summary now only shows a count line.

---

## 16. Search Page — Result Cards (`search-results.html`)

**File:** `gsearch/templates/gsearch/dataset-search/globus-portal-framework/components/search-results.html`

### Before
```html
{% for result in search.search_results %}
<div class="card my-3">
    <div class="card-header">
        <h3 class="search-title">
            <a href="{{ result.dataset_url }}">{{ result.title }}</a>
        </h3>
    </div>
    <div class="card-body">
        {% if result.dataset_type == 'H' %}
            <div class="mb-1 bg-warning ...">Historical dataset warning</div>
        {% endif %}
        {% for item in result.search_highlights %}
            <div class="my-1">
                {% if item.type == "date" %} ... date format ...
                {% elif item.title == "Description" %} ... truncated desc ...
                {% elif item.name == "format" or item.name == "tags" %} ... badges ...
                {% else %} <strong>{{ item.title }}:</strong> {{ item.value }} {% endif %}
            </div>
        {% endfor %}
    </div>
</div>
{% endfor %}
```

**What this was:** Bootstrap cards. Used `result.search_highlights` (the list of field/value pairs from `globus_search_fields.py`) to render each field generically.

### After
```html
{% load static %}
{% for result in search.search_results %}
<article class="gdex-dataset-result">

    <div class="gdex-dataset-result__thumb">
        <img src="{% static 'img/hero_earth.png' %}" alt="{{ result.title }}">
    </div>

    <div class="gdex-dataset-result__body">

        <!-- Title row -->
        <div class="gdex-dataset-result__top">
            <div class="gdex-dataset-result__title-block">
                <h3 class="gdex-dataset-result__title">
                    <a href="{{ result.dataset_url }}" data-summary="{{ result.summary }}">
                        {{ result.title }}
                        <i class="fas fa-arrow-up-right-from-square gdex-dataset-result__ext-icon"></i>
                    </a>
                </h3>
                <p class="gdex-dataset-result__doi">
                    DOI: {{ result.doi }}
                    {% if result.doi != 'N/A' %}
                    <button class="gdex-doi-copy" title="Copy DOI" data-doi="{{ result.doi }}">
                        <i class="fas fa-copy"></i>
                    </button>
                    {% endif %}
                </p>
            </div>
            <button class="gdex-dataset-result__cloud-btn" title="Cloud access">
                <i class="fas fa-cloud"></i>
            </button>
        </div>

        <!-- Historical warning -->
        {% if result.dataset_type == 'H' %}
        <div class="mb-2 bg-warning text-dark p-2 rounded" style="font-size:0.8rem;">
            <i class="fa-solid fa-triangle-exclamation"></i>
            For ancillary use only — not recommended as a primary research dataset...
        </div>
        {% endif %}

        <!-- Metadata rows -->
        <div class="gdex-dataset-result__meta">
            <span><strong>ID:</strong> {{ result.dataset_id }}</span>
            <span><strong>Size:</strong> {{ result.size }}</span>
            <span><strong>Data Type:</strong> {{ result.data_type_display }}</span>
            <span><strong>Temporal Range:</strong> {{ result.temporal_range }}</span>
            <span><strong>Data Source:</strong> {{ result.data_source }}</span>
        </div>
        <div class="gdex-dataset-result__meta">
            <span><strong>Data Format:</strong> {{ result.data_format_display }}</span>
            <span><strong>Time Resolution:</strong> {{ result.time_resolution_display }}</span>
        </div>

        <!-- Action buttons -->
        <div class="gdex-dataset-result__actions">
            <a href="{{ result.dataset_url }}" class="gdex-btn-access">
                <i class="fas fa-download"></i> Access Data
            </a>
            <a href="{{ result.dataset_url }}" class="gdex-btn-description">
                <i class="fas fa-file-alt"></i> Description
            </a>
            <a href="{{ result.dataset_url }}" class="gdex-btn-more">
                Citations &amp; Metrics <i class="fas fa-chart-bar ms-1"></i>
            </a>
        </div>

    </div>
</article>
{% empty %}
<p class="gdex-results-empty">No datasets found. Try adjusting your search or filters.</p>
{% endfor %}
```

**Key changes:**

| Change | Before | After |
|---|---|---|
| Element | `<div class="card">` | `<article class="gdex-dataset-result">` |
| Layout | Vertical card | Horizontal: thumbnail image left, body right |
| Fields shown | Loop over `search_highlights` list | Direct named properties: `result.doi`, `result.dataset_id`, `result.size`, etc. |
| DOI | Not shown | Shown with copy button (`data-doi` attribute, handled by JS) |
| Thumbnail | None | Square `hero_earth.png` placeholder (left side) |
| Actions | None | Three buttons: Access Data, Description, Citations & Metrics |
| Cloud button | None | `.gdex-dataset-result__cloud-btn` (hook for future Globus integration) |
| Title link | Bare `<a>` | `data-summary` attribute (used for hover popover), external link icon |
| Empty state | Nothing | `<p class="gdex-results-empty">` message |

---

## 17. Search Page — Base Template (`search-base.html`)

**File:** `gsearch/templates/gsearch/dataset-search/globus-portal-framework/search-base.html`

```diff
  {% block search_head %}
    <script src="{% static 'gsearch/js/gsearch.js' %}"></script>
    <link rel="stylesheet" href="{% static 'gsearch/css/gsearch.css' %}">
+   <link rel="stylesheet" href="{% static 'gsearch/css/search_data.css' %}">
  {% endblock %}
```

One line added: load `search_data.css` on every page that extends `search-base.html`. This is the correct place because the search CSS is needed across the full search page family.

---

## 18. Search Page — JavaScript (`search_data.js`)

**File:** `gsearch/static/gsearch/js/search_data.js`  
**Status:** New file (508 lines)

This file manages all client-side behavior for the redesigned search page. It is loaded at the bottom of `search.html` via `{% block extra_js %}`.

### Key sections:

**Group-based chip state management (lines 1–100)**
```javascript
var groupSelections = {};
var groupChipEls    = {};

// Each filter group (facet category) gets one chip in the active-filters bar
// showing all selected values as a comma-separated list
function renderGroupChip(groupKey) { ... }
function clearGroupChip(groupKey) { ... }
```

**Debounced navigation (lines 100–140)**
```javascript
var navTimer = null;
function scheduleNavigation() {
    clearTimeout(navTimer);
    navTimer = setTimeout(navigateWithFilters, 350);
}
function navigateWithFilters() {
    // Build URL params from all checked inputs + date pickers
    // Navigate to new URL (triggers Django re-render)
}
```

**URL state restoration (lines 140–200)**  
On page load, reads `window.location.search` and re-checks the corresponding checkboxes + updates chip state, so the UI stays in sync after navigation.

**Flatpickr date pickers (lines ~200–260)**  
Initializes flatpickr on `#temporal_start_input` and `#temporal_end_input` if flatpickr is available (CDN fallback: does nothing if library not loaded).

**Sidebar collapse toggle (lines ~260–300)**  
```javascript
document.querySelectorAll('[data-gdex-toggle]').forEach(function (header) {
    header.addEventListener('click', function () {
        var group = header.closest('.gdex-filter-group');
        group.classList.toggle('gdex-filter-group--collapsed');
        // rotate chevron icon
    });
});
```

**"See more" button (lines ~300–340)**  
Shows/hides filter options beyond the first N visible per group.

**Filter search input (lines ~340–380)**  
Inline text filter for each facet group: hides non-matching checkboxes as you type.

**DOI copy button (lines ~380–410)**  
```javascript
document.querySelectorAll('.gdex-doi-copy').forEach(function (btn) {
    btn.addEventListener('click', function () {
        navigator.clipboard.writeText(btn.dataset.doi).then(function () {
            // Show "Copied!" feedback for 1.5s
        });
    });
});
```

**Reset search (lines ~410–440)**  
```javascript
if (resetBtn) {
    resetBtn.addEventListener('click', function () {
        window.location.href = window.location.pathname; // strip all params
    });
}
```

**`clearFilters()` global function (lines ~440–480)**  
Called by the "clear all" link in the sidebar header. Unchecks all checkboxes and clears date inputs, then navigates.

---

## 19. Search Page — CSS (`search_data.css`)

**File:** `gsearch/static/gsearch/css/search_data.css`  
**Status:** New file (864 lines)

All styles for the search page redesign. Major sections:

### Hero banner (lines 1–120)
`.gdex-find-data-hero`: `min-height: 280px`, background image with `rgba(0,0,0,0.62)` overlay.  
`.gdex-find-data-hero__search-bar`: white input + blue search button, `overflow: hidden` for unified border-radius.

### Body layout (lines 120–200)
`.gdex-find-data-body`: sets `--waves-url` CSS custom property for the decorative wave background pattern.  
`.gdex-find-data-layout`: CSS Grid, `grid-template-columns: 280px 1fr` on desktop, single column on mobile.

### Sidebar (lines 200–380)
`.gdex-filters-sidebar`: white, `position: sticky; top: 0`, `max-height: 100vh; overflow-y: auto`.  
`.gdex-filter-group`: collapsible sections with chevron animation.  
`.gdex-filter-group--collapsed .gdex-filter-group__body { display: none }` — collapse state.  
`.gdex-filter-checkbox--count`: flex row with label on left, count badge on right.  
`.gdex-filter-date-input`: plain text inputs styled to match the sidebar aesthetic.

### Results area (lines 380–550)
`.gdex-results-count`: large count text above results.  
`.gdex-results-filters-row`: horizontal scrollable bar with active filter chips.  
`.gdex-active-filter-chip`: pill with group label, value, × remove button.  
`.gdex-btn-reset`: outlined button, right-aligned in the filters row.

### Result cards (lines 550–750)
`.gdex-dataset-result`: flex row, `gap: 1.5rem`, bottom border separator.  
`.gdex-dataset-result__thumb`: square image, `object-fit: cover`.  
`.gdex-dataset-result__meta`: `display: flex; flex-wrap: wrap; gap: 1rem` — metadata spans.  
`.gdex-dataset-result__actions`: flex row of three action buttons with distinct styles:
- `.gdex-btn-access`: solid blue (primary action)
- `.gdex-btn-description`: outline blue
- `.gdex-btn-more`: text-only with chart icon

### Cloud + copy buttons (lines 750–800)
`.gdex-dataset-result__cloud-btn` and `.gdex-doi-copy`: small icon-only buttons.

### Pagination (lines 800–840)
Restyled Bootstrap pagination to match the blue/navy color scheme.

### Mobile (lines 840–864)
Sidebar collapses above results on mobile (`grid-template-columns: 1fr`). Result card switches to vertical layout.

---

## 20. Globus Search — Field Extractors (`globus_search_fields.py`)

**File:** `gdexwebserver/settings/globus_search_fields.py`

This file defines Python functions that extract specific data from the raw Globus Search result JSON. Each function is mapped to a template variable name in `globus_search_indexes.py`.

### Existing extractors (refactored, not functionally changed)

- `search_highlights()` — reformatted for readability, simplified the field loop
- `title()`, `globus_app_link()`, `dataset_url()`, `https_url()`, `dataset_type()` — minor cleanup only

`dataset_url` was simplified:
```python
# Before
def dataset_url(result):
    url = result[0]["url"]
    parsed = urlsplit(url)
    return parsed.path

# After
def dataset_url(result):
    return urlsplit(result[0]["url"]).path
```

### New display name maps (added at top)
```python
_FORMAT_DISPLAY = {
    'netcdf4': 'NetCDF4', 'netcdf': 'NetCDF', 'proprietary_ascii': 'ASCII',
    'proprietary_binary': 'Binary', 'wmo_grib1': 'GRIB1',
    'noaa_imma': 'NOAA IMMA', 'dss_wmssc': 'DSS WMSSC',
}

_DATA_TYPE_DISPLAY = {
    'grid': 'Grid', 'platform_observation': 'Platform Observation',
    'satellite': 'Satellite', 'model_output': 'Model Output',
    'reanalysis': 'Reanalysis', 'derived_product': 'Derived Product',
}
```

### New internal helpers
```python
def _parse_time_res(raw):
    """'T : Monthly - < Annual'  →  'Monthly'"""
    return raw.split(' : ')[1].split(' - ')[0].strip() if ' : ' in raw else raw

def _fmt_date(raw):
    """'2023-01-15' or '2023-01-15T...' → '01-2023', or None on failure."""
    try:
        return datetime.strptime(str(raw)[:10], '%Y-%m-%d').strftime('%m-%Y')
    except (ValueError, TypeError):
        return None
```

### New extractors for redesigned result cards

| Function | Template variable | Returns |
|---|---|---|
| `summary(result)` | `result.summary` | Full description text (for hover popover) |
| `doi(result)` | `result.doi` | DOI string or `'N/A'` |
| `dataset_id(result)` | `result.dataset_id` | Short dataset ID or `'N/A'` |
| `size(result)` | `result.size` | `total_volume` field or `'N/A'` |
| `data_type_display(result)` | `result.data_type_display` | Display labels, comma-joined |
| `temporal_range(result)` | `result.temporal_range` | `'MM-YYYY – MM-YYYY'` or partial or `'N/A'` |
| `data_source(result)` | `result.data_source` | First contributor org, trimmed at `' > '` |
| `data_format_display(result)` | `result.data_format_display` | Display labels via `_FORMAT_DISPLAY` map |
| `time_resolution_display(result)` | `result.time_resolution_display` | Deduplicated resolution labels |

All new extractors return `'N/A'` on missing data, never raise exceptions.

---

## 21. Globus Search — Index Registration (`globus_search_indexes.py`)

**File:** `gdexwebserver/settings/globus_search_indexes.py`

The new field extractor functions are registered here so they become available as `result.fieldname` in templates:

```python
'fields': [
    # Existing (alignment-formatted):
    ("title",                   search_fields.title),
    ("globus_app_link",         search_fields.globus_app_link),
    ("dataset_url",             search_fields.dataset_url),
    ("https_url",               search_fields.https_url),
    ("dataset_type",            search_fields.dataset_type),
    ("search_highlights",       search_fields.search_highlights),
    # New for redesigned result cards:
    ("summary",                 search_fields.summary),
    ("doi",                     search_fields.doi),
    ("dataset_id",              search_fields.dataset_id),
    ("size",                    search_fields.size),
    ("data_type_display",       search_fields.data_type_display),
    ("temporal_range",          search_fields.temporal_range),
    ("data_source",             search_fields.data_source),
    ("data_format_display",     search_fields.data_format_display),
    ("time_resolution_display", search_fields.time_resolution_display),
],
```

---

## 22. Template Tag: `has_active_bucket`

**File:** `gsearch/templatetags/gsearch_tags.py`

```python
@register.filter
def has_active_bucket(facet):
    """Return True if any bucket in the facet is currently checked/selected."""
    try:
        buckets = facet.get('buckets') if isinstance(facet, dict) else getattr(facet, 'buckets', [])
    except Exception:
        return False
    for b in (buckets or []):
        checked = b.get('checked') if isinstance(b, dict) else getattr(b, 'checked', False)
        if checked:
            return True
    return False
```

Used in `search-sidebar.html` to decide whether a filter group should start expanded or collapsed:
```html
<div class="gdex-filter-group {% if not facet|has_active_bucket %}gdex-filter-group--collapsed{% endif %}">
```
Groups with active selections start expanded; all others start collapsed.

The implementation handles both dict-like and object-like facet structures (Globus Portal Framework can return either depending on the version).

---

## 23. Static Assets Added

| File | Size | Purpose |
|---|---|---|
| `gdexwebserver/static/img/hero_earth.png` | ~6.3 MB | Hero background image used on homepage and search page |
| `gdexwebserver/static/img/20cr_v3.png` | ~41 KB | Alternate placeholder for popular dataset cards |

Both images are referenced via `{% static 'img/...' %}` in templates. `hero_earth.png` is also used as the metrics section background.

---

## 24. Removed / Cleaned Up Code

### Removed: `search-nav` tabs
The original `search.html` had a tab bar (Search / About) managed by `components/search-nav.html`. The new design removed the tab structure entirely — the About tab content is gone from the search page. The `search-nav.html` component still exists but is no longer included.

### Removed: `datasets/migrations/0003_customsubsetpage.py` and `datasets/models.py` changes
A `CustomSubsetPage` model that existed in the `siparcs26` branch was removed. This was likely experimental code that was cleaned up before it could cause migration conflicts.

### Removed: Old location filter code in `search_data.js`
The original `search_data.js` contained specific location-based filter handling logic that was removed during the `8ffcfd28` commit ("remove unused location filter code"). Location filtering still works through the standard Globus facets in the sidebar.

### Removed: Sticky "TEST INSTANCE" banner
The yellow Bootstrap `alert-warning` sticky banner was replaced with a compact red header bar (see [Section 4](#4-global-header-changes)).

### Removed: `flatpickr` CDN link from templates
The `f44de343` commit removed direct CDN `<script>` and `<link>` tags for flatpickr from the HTML and added a guard in JS:
```javascript
// Only init if flatpickr is available
if (typeof flatpickr !== 'undefined') {
    dateFromPicker = flatpickr('#temporal_start_input', { ... });
    dateToPicker   = flatpickr('#temporal_end_input',   { ... });
}
```

---

## 25. Files NOT Changed (Original Pages)

These files exist on `main` and were **not modified** on `siparcs26`:

| File | Why untouched |
|---|---|
| `home/templates/home/home_page.html` | Original homepage — only a debug `<p>` tag was added (see `home_page.html` diff — minor) |
| `home/templates/home/home_grid_cards.html` | Original feature cards for `HomePage` |
| `home/templates/home/home_search_bar.html` | Original search bar for `HomePage` |
| `home/templates/home/splash.html` | Metrics splash page — untouched |
| `home/urls.py` | No URL routing changes needed |
| `home/views.py` | No view changes needed |
| All `gsearch/` templates except those listed | Detail pages, pagination, etc. untouched |

---

## 26. Commit History (Meaningful Commits Only)

Listed newest-to-oldest (CI image bump commits omitted):

| Commit | Message | Files Affected |
|---|---|---|
| `c4db6d07` | Refactor metrics section styles: remove background gradient and enhance text shadow | `home_page.css` |
| `76beefbb` | Update metrics section styles and set background image dynamically | `home_page.css`, `test_home_metrics.html` |
| `8ffcfd28` | Update header links to GDEX test home page; remove unused location filter code | `header_ncar_logo.html`, `search_data.js` |
| `3741297b` | Refactor search summary and filters display; update labels and add reset button | `search-summary.html`, `search.html`, `search_data.css` |
| `f44de343` | Initialize flatpickr only if library is loaded; remove unnecessary CDN links | `search_data.js`, search templates |
| `b9b047d5` | Enhance search: update CSS for hero section, improve JS for location filtering | `search_data.css`, `search_data.js` |
| `79aa04b1` | Add JavaScript functionality for GDEX search data page | `search_data.js` |
| `e8ed0022` | Add filter sidebar and enhance JS for data search | `search-sidebar.html`, `search_data.js` |
| `c1226ff6` | Enhance search: add new field extractors, update search results template, refine CSS | `globus_search_fields.py`, `search-results.html`, `search_data.css` |
| `988da2aa` | Fix typo in hero description text | `test_home_page.html` |
| `8a5ddbfe` | Implement new search page design with hero banner and search functionality | `search.html`, `search_data.css` |
| `22626aaa` | Increase padding on Explore Datasets section | `home_page.css` |
| `fd45af6e` | Add new image to popular datasets card | `20cr_v3.png` added |
| `5977fc15` | Wire Wagtail model fields into feature cards; redesign search dataset card | `test_home_grid_cards.html`, `search-results.html` |
| `05aac653` | Update search dataset card CSS | `search_data.css` |
| `c24344ba` | Remodel search for dataset card | `search-results.html`, `search_data.css` |
| `34efa678` | Adjust chip width; add scroll restoration handling | `home_page.css`, `test_home_search_bar.html` |
| `75926e6c` | Refactor metrics and features sections: adjust padding, update styles | `home_page.css` |
| `6692d198` | Refactor styling for metrics section | `home_page.css` |
| `e9440162` | Enhance metrics section: add background image, adjust layout | `home_page.css`, `test_home_metrics.html` |
| `a456db85` | Refactor metrics section: center align, adjust padding | `home_page.css`, `test_home_metrics.html` |
| `07e5cda5` | Refactor metrics section: update layout, enhance featured styling | `home_page.css`, `test_home_metrics.html` |
| `acfbc05d` | Enhance metrics section: add background image | `test_home_metrics.html` |
| `36ab4009` | Add count-up animation to homepage metrics section | `test_home_metrics.html` |
| `391ed9cc` | Enhance layout: update background properties | `home_page.css` |
| `a5bbe0e3` | Fix search input reset on page show event | `test_home_search_bar.html` |
| `f4aa2785` | Enhance layout: update background images for features and metrics | `home_page.css` |
| `9f65b0a1` | Enhance layout: add background images to feature/metrics sections | `home_page.css` |
| `3480915f` | Refactor layout: enforce padding rules on test home page | `home_page.css`, `test_home_page.html` |
| `f76974b8` | Refactor layout/responsiveness: adjust padding, dataset card sizes, swiper breakpoints | `home_page.css` |
| `ed0083df` | Enhance dataset display: add size and user metrics to dataset cards | `test_home_popular_datasets.html` |
| `dd3edd53` | Refactor header/metrics: remove test warning, update metric icons, adjust layout | `header_decs.html`, `test_home_metrics.html`, `home_page.css` |
| `d4b2f779` | Add metrics section to home page with dynamic data fetching | `test_home_metrics.html`, `test_home_page.html` |
| `e6c6398d` | Remove popular datasets from grid cards; ensure proper block structure | `test_home_grid_cards.html`, `test_home_page.html` |
| `a1300914` | Add popular dataset section | `test_home_popular_datasets.html` |
| `dbb1e540` | Add popular datasets section with swiper functionality | `test_home_popular_datasets.html`, `test_home_page.html` |
| `737592b9` | Add waves wrapper and feature cards section to home grid template | `home_page.css`, `test_home_page.html` |
| `c1511152` | Update button color to use !important; remove search suggestions from chips section | `home_page.css`, `test_home_search_bar.html` |
| `67ca99e3` | Add new search section and chips to TestHomePage | `test_home_search_bar.html` |
| `1a412530` | Add hero section to TestHomePage template | `test_home_page.html` |
| `90f3bda8` | Refactor hero section to use dynamic banner image if available | `test_home_page.html` |
| `d8593ae9` | Add hero earth image for enhanced visual content | `hero_earth.png` added |
| `e4f4070e` | Refactor breadcrumb block in base and test home page templates | `base.html`, `test_home_page.html` |
| `07c399c2` / `bf909bcc` / `d37a058a` | Fix/refactor hero background image markup | `test_home_page.html`, `home_page.css` |
| `f0bea77f` | Add hero section to TestHomePage with customizable fields and styles | `home_page.css`, `test_home_page.html` |
| `d77a554f` | Add new banner image field in models | `home/models.py`, migration |
| `60058f86` | Remove "Suggestions:" label from search suggestions | `test_home_search_bar.html` |
| `0e15cbca` | Add FeaturedCard model and refactor HomePage to use dynamic featured cards | `home/models.py`, migration |
| `8c0ee1f5` | Refactor home grid cards to dynamically render card content and icons | `test_home_grid_cards.html` |
| `9fe433fe` | Update JupyterHub card text for clarity | CMS content |

---

## 27. Location Cascade Filter (`search-sidebar.html`, `search_data.js`)

Replaced flat location checkboxes with a three-level cascade: **Continent → Country → State/Province**.

### How it works
- Three `<select>` dropdowns live in the sidebar above the location facet checkboxes.
- Selecting a continent populates the country dropdown; selecting a country populates the state dropdown.
- Each selection inserts a hidden checkbox into `#facet-form` and calls `customSearch(1)`.
- On page reload the active URL params (`filter-term.location_*`) are read and the dropdowns are restored to their previous state via `window._restoreLocationSelects()`.

### Files changed
| File | Change |
|---|---|
| `search-sidebar.html` | Added continent/country/state `<select>` elements above location facet group |
| `search_data.js` | Added `classifyBucket()`, cascade populate logic, hidden checkbox injection, URL-based restore via `_restoreLocationSelects()` |
| `search_data.css` | Styles for `.gdex-location-cascade` dropdowns |

---

## 28. Selected Filters Chip System (`search.html`, `search_data.js`, `gsearch/views.py`)

Chips in the "Selected Filters" bar now reliably remove their filter when × is clicked.

### Bugs fixed
| Bug | Root cause | Fix |
|---|---|---|
| Temporal chip × didn't remove filter | `customSearch(1)` re-added `filter-range.temporal_range_end` from the URL before the form could strip it | `gdexClearTemporal()` now delegates to `clearTemporalRange()` which calls `removeUrlParameter()` first |
| `gdexRemoveFilter()` silently failed for values with special chars (`.`, `>`) | CSS attribute selector `[value="..."]` mis-parsed special chars | Replaced with DOM iteration using `inp.name === name && inp.value === value` |
| Reset Search button did nothing | No `onclick` handler wired up | Added `onclick="gdexResetSearch();"` and defined `gdexResetSearch()` that clears preset radios, resets location selects, and calls `clearFilters()` |
| `clearFilters()` left temporal URL params in the address bar | `$('#facet-form').submit()` didn't strip temporal params first | Added `removeUrlParameter()` calls for both temporal params before form submit |

### Files changed
| File | Change |
|---|---|
| `search.html` | Added `onclick="gdexResetSearch();"` to Reset Search button; updated chip `onclick` handlers |
| `search_data.js` | Rewrote `gdexRemoveFilter()`, `gdexClearTemporal()`, `gdexResetSearch()`; updated `clearFilters()` |

---

## 29. Temporal Preset Improvements (`gsearch/views.py`, `search.html`, `search-sidebar.html`)

"Last 1 / 5 / 10 / 25 year" radio buttons no longer fill the custom From/To date fields, and the selected preset is restored correctly on page refresh.

### Changes
- **`gsearch/views.py`**: After every search request, parses `filter-range.temporal_range_end` from GET params and saves `temporal_start_input` / `temporal_end_input` to the Django session. Also detects if the active date range matches a 1/5/10/25-year preset (±1 day tolerance) and saves `temporal_preset_years` to session.
- **`search.html`**: `gdexApplyPreset()` no longer writes to the visible From/To inputs. Instead it clears them, removes temporal URL params via `removeUrlParameter()`, injects a hidden `<input name="filter-range.temporal_range_end">` directly into `#facet-form`, then calls `customSearch(1)`. Preset radios are restored server-side via `{% if request.session.temporal_preset_years %}`. The time chip label shows "Last X years" for presets and raw dates for custom ranges.
- **`search-sidebar.html`**: From/To fields are only pre-populated from session when `temporal_preset_years` is **not** set; date `onchange` deselects preset radios automatically.

### Files changed
| File | Change |
|---|---|
| `gsearch/views.py` | Added temporal parsing block and preset detection block; imports `date as _date` |
| `search.html` | Rewrote `gdexApplyPreset()`; updated chip template; added preset radio restore script |
| `search-sidebar.html` | Conditional pre-population of From/To fields; `onchange` deselects presets |

---

## 30. Browse Datasets Card URL Fix (`home/templates/home/test_home_grid_cards.html`, `home/migrations/`)

### Template fix
The feature card link template now distinguishes internal vs external URLs:
- `card_page` set → uses Wagtail page URL (no `target="_blank"`)
- `card_url` starting with `/` → internal link, no new tab
- `card_url` starting with `http` → external link, opens in new tab

Previously all `card_url` values received `target="_blank"`, causing internal paths to open in a new tab.

### Data migration
`home/migrations/0015_fix_browse_datasets_card_url.py` — data migration that finds any `TestHomePageFeaturedCard` / `FeaturedCard` record where the title contains "browse" + "dataset" or the linked page resolves to an old search URL (`/lookfordata/`, `/find-data/`, etc.), and updates it to `card_url = '/gsearch/dataset-search/'` with `card_page_id = None`.

> **Note:** This migration has been written to disk but not yet applied. Run `python3 manage.py migrate home 0015` when ready.

### Files changed
| File | Change |
|---|---|
| `test_home_grid_cards.html` | Three-branch link logic: Wagtail page / internal URL / external URL |
| `home/migrations/0015_fix_browse_datasets_card_url.py` | New data migration (not yet applied) |

---

## 31. Non-Scrollable Filter Sidebar (`search_data.css`, `search_data.js`, `search-sidebar.html`)

The filter sidebar previously had a fixed `max-height: calc(100vh - 2rem)` with an internal scroll body, causing user friction.

### Changes
- Removed `max-height`, `overflow: hidden`, `overflow-y: auto`, and all scrollbar styles from `.gdex-filters-sidebar` and `.gdex-filters-sidebar__scroll-body`.
- Added `align-self: flex-start` so the sticky sidebar doesn't stretch to match the results column height.
- Removed the `::after` fade-gradient overlay and `.gdex-filters-sidebar--at-bottom` class.
- Removed the `checkScroll()` JS function and its `scroll` event listener from `search_data.js`.
- Removed `id="gdex-sidebar-body"` from the sidebar template (no longer referenced by JS).

The sidebar now expands to its full natural height and the user scrolls the whole page normally.

### Files changed
| File | Change |
|---|---|
| `search_data.css` | Removed scroll/overflow/scrollbar/fade-gradient rules; added `align-self: flex-start` |
| `search_data.js` | Removed `checkScroll()`, `sidebarBody` variable, and scroll event listener |
| `search-sidebar.html` | Removed `id="gdex-sidebar-body"` |

---

## 32. Homepage Hero & Chip Polish (`home/static/css/home_page.css`, `test_home_search_bar.html`)

### Hero heading color
`GDEX` highlight in the hero heading changed to `#0057c2` — the same blue used by the "Browse Datasets" primary button — for visual consistency.

### Hero overlay
Dark overlay (`rgba(0,0,0,0.50)`) restored after a brief experiment with removing it; ensures hero text remains readable against any banner image.

### Explore chips icon size
Icons inside the "Explore specialized datasets" chips increased from `1.1rem` → `1.8rem`, with icon-to-text spacing increased from `me-2` → `me-3`, to better balance with the two-line chip text.

### Files changed
| File | Change |
|---|---|
| `home_page.css` | `.gdex-hero__heading-highlight` color `→ #0057c2`; overlay restored; chip icon `font-size: 1.8rem` |
| `test_home_search_bar.html` | Icon spacing `me-2 → me-3` on both chip icons |

---

## 33. Ancillary Dataset Badge (`search-results.html`, `search_data.css`)

The large orange warning box for historical/ancillary datasets (`dataset_type == 'H'`) was replaced with a compact inline badge that sits between the dataset title and the DOI line.

### Before
Full-width `bg-warning` `<div>` spanning the card body, significantly inflating card height.

### After
A small `<p class="gdex-ancillary-badge">` element with `#faa119` background (the Unity theme warning color), tight padding, and 6px border radius. The full message — *"Ancillary use only — not recommended as a primary research dataset. Likely superseded by newer datasets."* — is always visible inline; no hover required.

### Files changed
| File | Change |
|---|---|
| `search-results.html` | Replaced `<div class="bg-warning ...">` with `<p class="gdex-ancillary-badge">` inside `title-block` |
| `search_data.css` | Added `.gdex-ancillary-badge` styles using Unity `#faa119` warning color |

---

## 34. Specialized Dataset Pages — AI-Ready & Popular (`gsearch/`)

Two new standalone pages that surface specialized dataset collections, replacing external links to the metrics page.

### AI-Ready Datasets — `/gsearch/ai-ready/`
- Calls `get_AI_datasets()` from `api.common`, which queries `search.datasets WHERE ai_ready = 'Y'`.
- Renders up to 200 datasets as search-style cards with title, dataset ID, Access Data / Description buttons, and an "AI-Ready" badge.
- Auto-grows as new datasets are tagged `ai_ready = 'Y'` in the database — no manual curation needed.

### Popular Datasets — `/gsearch/popular/`
- Calls `get_top_datasets()` from `api.common`, which reads the `rankingsYear.json` file (top 50).
- Renders cards with rank number, title, unique users count, and volume downloaded.
- Auto-updates whenever the rankings file is refreshed.

### Homepage wiring
- "AI-ready datasets" chip on homepage: changed from external `https://gdex.ucar.edu/metrics/by-the-numbers/` → `/gsearch/ai-ready/`
- "View all datasets" link in Popular Datasets section: changed from same external URL → `/gsearch/popular/`

### Files changed
| File | Change |
|---|---|
| `gsearch/urls.py` | Added `ai-ready/` and `popular/` routes before the catch-all `<dssearch:index>/` |
| `gsearch/views.py` | Added `ai_ready_datasets()` and `popular_datasets()` views; imported `get_AI_datasets`, `get_top_datasets` |
| `gsearch/templates/gsearch/ai-ready-datasets.html` | New template extending `base.html` |
| `gsearch/templates/gsearch/popular-datasets.html` | New template extending `base.html` |
| `gsearch/static/gsearch/css/specialized.css` | New shared CSS for both pages (`.gdex-specialized-*` classes) |
| `test_home_search_bar.html` | AI-ready chip href → `/gsearch/ai-ready/` |
| `test_home_popular_datasets.html` | "View all" href → `/gsearch/popular/` |

---

*Sections 27–34 added 2026-06-27 covering changes made after initial branch setup.*

---

## 35. Pagination Redesign (`search-pagination.html`, `search_data.css`)

Replaced the default Bootstrap pagination with a clean custom design matching modern UI conventions.

### Before
Bootstrap `.pagination` list with `page-item` / `page-link` classes, styled inconsistently. Title text ("Search results page navigation") was inside a `<div>` above the nav.

### After
- Custom `.gdex-pagination__list` with `<button>` elements for every control.
- **Active page**: filled blue rounded square (`#0057c2`) with white text.
- **Inactive pages**: plain blue text, light blue background on hover — no border.
- **Arrows**: `<` `>` for prev/next, `«` `»` for first/last — all grayed out and `disabled` when at the boundary.
- **Label**: `<p class="gdex-pagination__label">Search results page navigation (N pages)</p>` restored above the nav, bold, centered. Correctly pluralises ("1 page" vs "166 pages").

### Files changed
| File | Change |
|---|---|
| `search-pagination.html` | Full rewrite using `gdex-pagination__*` classes and `<button>` elements |
| `search_data.css` | Replaced Bootstrap pagination overrides with `.gdex-pagination__label`, `.gdex-pagination__list`, `.gdex-pagination__page`, `.gdex-pagination__arrow`, `.gdex-pagination__ellipsis` |

---

## 36. Hero Heading GDEX Color (`home/static/css/home_page.css`)

The "GDEX" highlight in the hero heading was changed to `#faa119` — the Unity theme warning/accent orange — so the platform name stands out visually from the surrounding white heading text against the dark hero overlay.

| Property | Value |
|---|---|
| CSS rule | `.gdex-hero__heading-highlight { color: #faa119; }` |
| Rationale | Orange is already part of the Unity brand palette; it pops strongly on the dark hero background without clashing with the blue CTA buttons |

---

## 37. Specialized Pages — Spacing & Navigation (`ai-ready-datasets.html`, `popular-datasets.html`)

The AI-ready and Popular dataset pages had excessive whitespace at the top because both the `base.html` `<main>` tag (`py-3 pt-md-4`) and the inner container (`py-5`) were adding vertical padding.

### Fix
- Overrode `{% block main_class %}` in both templates to `container-lg pb-4` (removes the default top padding from base).
- Changed the inner wrapper from `<div class="container-lg py-5">` to `<div class="pt-3">` for a compact, correctly spaced layout.

### Files changed
| File | Change |
|---|---|
| `gsearch/templates/gsearch/ai-ready-datasets.html` | `main_class` block override; reduced inner top padding |
| `gsearch/templates/gsearch/popular-datasets.html` | `main_class` block override; reduced inner top padding |

---

## 38. Custom Temporal Range — Apply Button & Reset Fix (`search-sidebar.html`, `search.html`, `search_data.css`)

### Problems fixed

**1. Filter fired after entering only the From date**
Both date inputs had `onchange="... customSearch(1);"` which triggered a search as soon as the first field was filled, creating an incomplete range. Users had no chance to enter the To date before results updated.

**2. Cancelling the temporal chip didn't reset the date inputs**
The jQuery UI datepicker held internal state that wasn't cleared when the chip × was clicked, so the From/To fields appeared to retain their values after removal.

### Solution

- **Removed `onchange`** from both `#temporal_start_input` and `#temporal_end_input`.
- **Added an "Apply Range" button** (`gdex-temporal-apply-btn`) below the date inputs. The button calls `gdexApplyCustomTemporal()` which validates that **both** fields have values before calling `customSearch(1)` — no partial-range searches.
- **Updated `gdexClearTemporal()`** in `search.html` to explicitly reset the jQuery UI datepicker via `datepicker('setDate', null)` on both inputs AND clear the raw `.value` property before delegating to `clearTemporalRange()`.

### Files changed
| File | Change |
|---|---|
| `search-sidebar.html` | Removed `onchange` from both date inputs; added "Apply Range" `<button>` |
| `search.html` | Added `gdexApplyCustomTemporal()` function; updated `gdexClearTemporal()` to reset datepicker and clear values explicitly |
| `search_data.css` | Added `.gdex-temporal-apply-btn` styles (full-width blue button) |

---

*Sections 27–38 added 2026-06-27 covering changes made after initial branch setup.*  
*Document generated from `git diff main..siparcs26` and `git log main..siparcs26 --oneline --no-merges`.*  
*Branch: `siparcs26` | Compared against: `main`*
