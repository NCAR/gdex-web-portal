# Dataset file list templates

How the dataset "Data Access > File list" view is built. Everything below lives in
`datasets/templates/datasets/` unless noted.

## Request flow

1. The browser (or an in-page link) requests `/datasets/<dsid>/filelist/[<gindex>/]` which maps to
   `datasets/views.py: get_filelist_table` (see `datasets/urls.py`).
2. The view calls the internal API (`/api/datasets/<dsid>/filelist/...`, built in `api/common.py`),
   adds `is_ajax` / `is_glade` flags, and renders `filelist.html`.
3. The response is injected into the dataset page by `replace_ds_content()`. Links inside the list
   (subgroups, Back, pagination, filters) fetch the next list the same way via `$.get`.
4. `filelist.html` loads `static/js/cache_filelist.js` and `static/datasets/css/filelist.css` each time
   it renders, so JS handlers that must not stack are unbound first (`$(document).off('.accessOptions')`).

`data` (context) holds the dataset-wide info: `dsid`, `title`, `groups`, `is_glade`, `is_ajax`,
`locflag`, `filter_wfile`, `parent`. Each entry of `data.groups` is a `Group` (`api/common.py`) with
`group_id`, `title`, `gindex`, `column_headers`, `rows`, `paginator`, `total_file_count`,
`is_group_summary`, `has_thredds`. Each row is a list of cell dicts (`name`, `value`, `url`,
`data_path`, `is_file`, `meta_link`, ...); the first cell is the file name.

## Templates

| Template | Purpose |
|----------|---------|
| `filelist.html` | Entry point. Page header (title, Back link, notes), the preview modal, the subgroup summary, then loops over `data.groups` to render each group's summary, filter, pagination and table. Chooses the Zarr/ARCO views when the data format is zarr (or the group index is negative). |
| `filelist-subgroup-table.html` | "Subgroup Summary" table shown when there is more than one group: group links, descriptions, file counts, and the group-wide checkboxes (`.parent_group`). |
| `filelist-table-summary.html` | Per-group header block: file count, download instructions, download/glade buttons (`download_buttons.html` / `glade_buttons.html`), and the "N files selected / Clear Selections" line. Shown for groups with more than one file. |
| `filelist-filter.html` | File name filter. Paginated groups (>2000 files) or already-filtered lists use the server-side filter (`?filter_wfile=`, glob, case-sensitive). Smaller groups get an instant in-browser filter (`.page-filter-input`, handled in `cache_filelist.js`). |
| `filelist-pagination.html` | Page navigation for paginated groups (`group.paginator`). Page indexes are 0-based in the view and shown 1-based here. |
| `filelist-table.html` | The table for one group. File groups show only **Index** (checkbox + number) and the **file name** (with a chevron). A hidden `.file-detail` row under each file holds the other columns (Size, Data Format, Date Archived, ...) and the access buttons. Summary groups (`is_group_summary`) render all columns as a plain table. |
| `filelist-cell.html` | Content of one cell: file/ajax/zarr links, glade path text, formatted size, or plain value. Included for both the main cell and the detail-row values. |
| `filelist-access-options.html` | The per-file buttons: download, copy glade path, preview (.nc), THREDDS (TDS) access, detailed metadata. Included from the detail row. |
| `filelist-arco-button.html` | The button(s) for a Zarr/ARCO catalog entry (copy full link / path), used from `filelist-cell.html`. |
| `filelist-zarr-catalogs.html` | Table of ARCO/Zarr catalogs archived under negative group indexes. Rendered by the `show_arco_catalogs` tag in `home/templatetags/custom_tags.py`. |
| `filelist-zarr-files.html` | Table of Zarr directories/files under normal groups. Rendered by the `show_zarr_files` tag. |
| `request_filelist.html` / `base_request.html` | The separate file list for a data request (not a dataset group). Reuses `cache_filelist.js` and the same `.file` / `btn-all-files` / `clear-group-btn` conventions. |
| `download_buttons.html` / `glade_buttons.html` | Script/Globus download buttons (web) or "Get Filelist" button (glade/HPC). |

## Static assets

- `static/js/cache_filelist.js` (project `gdexwebserver/static/js/`): all behavior. Main pieces:
  - selection: `toggleSingleBox`, `toggleChildBoxes`, `selectAllFiles`, `clearFileSelections`,
    `setTableSummary` (hidden rows from the page filter are skipped; see `visibleCheckboxes`)
  - per-file UI: `toggleFileDetail` (chevron), `copyPathClicked`, `previewFileClicked`
  - `pageFilterChanged` / `pageFilterCleared` (client-side filter), `sortColumn`
  - downloads: `getCheckedFiles`, `getScript`, `showSelectionConfirmation` (used by `convertFiles` and
    `showGlobusConfirmation`), `sendConvertApp`, `globusTransfer`
- `static/datasets/css/filelist.css`: checkbox styling, `.filelist-table` fixed layout, and the instant
  `data-tip` tooltips used by the file buttons.

## Conventions and gotchas

- **Included templates do not inherit `{% load %}`.** Every partial that uses custom filters needs its own
  `{% load custom_tags %}` (e.g. `get_extension`, `make_glade_URL`).
- **Browser caching:** `cache_filelist.js` is a static file; after changing it, hard-refresh (or bump the
  static version) or you will test the old code.
- **Row structure:** each file is two `<tr>`s, the main row and its `.file-detail` row. Code that walks or
  re-orders rows (sorting, range select, filtering) must keep them together; the file size lives on
  the main row as `data-size`.
- **Name column assumption:** the file name is the first cell of every row (`row.0`); Index is the first
  `<td>`, the name the second.
- **Tooltips:** use `data-tip` (CSS, instant) rather than `title` (slow native tooltip).
- **Thresholds:** the 2000-file page size is in `api/common.py`; the filter template switches modes
  on `group.paginator.needs_pagination`.
