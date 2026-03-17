# GDEX Favicon Setup Instructions

1. Go to [RealFaviconGenerator](https://realfavicongenerator.net) and upload the standard (blue) GDEX icon (PNG format).

2. **Configuration:**
   - **Dark icon:** Select 'Use another icon' and choose the white GDEX icon (PNG format).
   - **Apple Touch Icon:** Select 'Add a plain background and margins'. Set color to white (`#ffffff`) and set image size to largest setting. Set App name = `GDEX`.
   - **Web app manifest:** Set Name = `NCAR GDEX` and Short name = `GDEX`. Select 'Add a plain background and margins'. Set image size to largest setting. Set background and theme color to white (`#ffffff`).
   - **Favicon path:** Set favicon path = `/img/app-favicons/gdex/`

3. Download your package.

4. Extract this package in `/gdexwebserver/static/img/app-favicons/gdex/`. This should create the following files in that directory:
   - `apple-touch-icon.png`
   - `favicon-96x96.png`
   - `favicon.ico`
   - `favicon.svg`
   - `site.webmanifest`

5. Insert the following code in `/gdexwebserver/templates/unity/icons.html`, replacing the existing code that references the old favicon files. Place this after the line `{% load static %}` and before any other code in that file:

```html
<link rel="icon" type="image/png" href="{% static 'img/app-favicons/gdex/favicon-96x96.png' %}" sizes="96x96" />
<link rel="icon" type="image/svg+xml" href="{% static 'img/app-favicons/gdex/favicon.svg' %}" />
<link rel="shortcut icon" href="{% static 'img/app-favicons/gdex/favicon.ico' %}" />
<link rel="apple-touch-icon" sizes="180x180" href="{% static 'img/app-favicons/gdex/apple-touch-icon.png' %}" />
<meta name="apple-mobile-web-app-title" content="GDEX" />
<link rel="manifest" href="{% static 'img/app-favicons/gdex/site.webmanifest' %}" />
```
