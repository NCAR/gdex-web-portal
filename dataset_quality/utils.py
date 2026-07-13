""" Placeholder data standing in for DatasetQualityAssessment rows until the
models in dataset_quality/models.py are migrated and real assessments are
curated. 'd084001' is a worked example with fake but representative
criteria; every other dataset has no rows, so no Quality Checklist tab is
shown for it. """

TIER_ORDER = ["Acceptable", "Analysis Ready", "AI-Optimized"]

DIMENSION_ORDER = [
    "Prepared and Consistent",
    "High Quality",
    "Well-documented",
    "Analysis-ready",
    "Findable and accessible",
    "Clearly licensed",
]

FAKE_ASSESSMENTS = {
    "d084001": [
        # Prepared and Consistent
        {"dimension": "Prepared and Consistent", "criterion": "Missing values",
         "description": "How absence of expected data values are encoded in "
                         "data files and communicated to users.",
         "tier": "Acceptable", "met": True,
         "note": "Missing value encoding (_FillValue) is documented in the "
                 "file header and consistent across all files."},
        {"dimension": "Prepared and Consistent", "criterion": "Outlier identification",
         "description": "Whether anomalous values have been considered, "
                         "flagged, documented, or otherwise distinguished "
                         "from typical values.",
         "tier": "Analysis Ready", "met": True,
         "note": "Values outside the physically plausible range are "
                 "flagged with a QC flag variable."},
        {"dimension": "Prepared and Consistent", "criterion": "Format regularity",
         "description": "Whether data are stored in a structured, "
                         "machine-readable, non-proprietary file format "
                         "with internally consistent conventions across "
                         "all files.",
         "tier": "Acceptable", "met": True,
         "note": "All files are distributed as NetCDF4-classic with "
                 "consistent variable names and dimension ordering."},
        {"dimension": "Prepared and Consistent", "criterion": "Spatial/temporal regularity",
         "description": "Whether data are organized on a predictable grid "
                         "or at consistent time intervals, or irregularity "
                         "is explicitly documented.",
         "tier": "Analysis Ready", "met": True,
         "note": "Data are provided on a regular 0.25-degree grid at "
                 "6-hourly intervals."},
        {"dimension": "Prepared and Consistent", "criterion": "Data types and encoding",
         "description": "Whether variables use appropriate computational "
                         "types and encoding choices are consistent, "
                         "documented, and decodable by common tools.",
         "tier": "Analysis Ready", "met": True,
         "note": "Float32 with CF-compliant scale/offset and calendar "
                 "attributes."},

        # High Quality
        {"dimension": "High Quality", "criterion": "Completeness",
         "description": "The extent to which a dataset covers its intended "
                         "spatial domain, temporal range, and variable "
                         "set.",
         "tier": "Analysis Ready", "met": False,
         "note": "A known temporal gap (2016-2017) is not yet documented "
                 "in the dataset metadata."},
        {"dimension": "High Quality", "criterion": "Internal consistency",
         "description": "The uniformity of representational conventions "
                         "across the dataset's full spatial, temporal, and "
                         "file extent.",
         "tier": "Analysis Ready", "met": True,
         "note": "Units and variable names verified consistent across all "
                 "files by curator review."},
        {"dimension": "High Quality", "criterion": "Bias characterization",
         "description": "Whether known systematic deviations from true "
                         "values have been identified, described, and "
                         "quantified.",
         "tier": "AI-Optimized", "met": False,
         "note": "Instrument calibration bias has not yet been "
                 "quantified."},
        {"dimension": "High Quality", "criterion": "Quality control",
         "description": "The systematic procedures applied to identify and "
                         "handle erroneous or anomalous values, and their "
                         "documentation.",
         "tier": "Analysis Ready", "met": True,
         "note": "Automated QC pipeline applied; outcomes summarized in "
                 "the Documentation tab."},
        {"dimension": "High Quality", "criterion": "Provenance tracking",
         "description": "The documented history of a dataset's origins and "
                         "transformations.",
         "tier": "AI-Optimized", "met": True,
         "note": "Full processing lineage recorded in the Provenance "
                 "tab."},
        {"dimension": "High Quality", "criterion": "Integrity verification",
         "description": "The assurance that data have not been corrupted, "
                         "truncated, or silently modified during storage, "
                         "transfer, or processing.",
         "tier": "AI-Optimized", "met": False,
         "note": "Checksums are not yet published for all files."},

        # Well-documented
        {"dimension": "Well-documented", "criterion": "Dataset-level metadata",
         "description": "Descriptive information applying to the dataset "
                         "as a whole.",
         "tier": "Acceptable", "met": True,
         "note": "Abstract, coverage, and version are documented on the "
                 "Description tab."},
        {"dimension": "Well-documented", "criterion": "Variable-level documentation",
         "description": "Per-variable descriptions including name, "
                         "physical meaning, units, valid range, and "
                         "null-value encoding.",
         "tier": "Acceptable", "met": True,
         "note": "A full data dictionary is provided in the Documentation "
                 "tab."},
        {"dimension": "Well-documented", "criterion": "Collection/generation methods",
         "description": "Documentation of how the data were produced: "
                         "instruments, model configuration, algorithm, or "
                         "processing chain.",
         "tier": "Analysis Ready", "met": True,
         "note": "Instrument and processing chain are described in the "
                 "Documentation tab."},
        {"dimension": "Well-documented", "criterion": "Citation information",
         "description": "How users should credit the dataset, including a "
                         "recommended citation string and persistent "
                         "identifiers.",
         "tier": "Acceptable", "met": True,
         "note": "Recommended citation and DOI are listed on the Citation "
                 "tab."},
        {"dimension": "Well-documented", "criterion": "Usage guidance",
         "description": "Information about appropriate and inappropriate "
                         "uses of the dataset, known limitations, and "
                         "conditions shaping interpretation.",
         "tier": "Analysis Ready", "met": False,
         "note": "An explicit in-scope/out-of-scope usage section has not "
                 "yet been written."},

        # Analysis-ready
        {"dimension": "Analysis-ready", "criterion": "Machine-readable catalogs",
         "description": "A structured, programmatically queryable index of "
                         "the dataset's contents, extent, and access "
                         "endpoints.",
         "tier": "Analysis Ready", "met": True,
         "note": "A STAC catalog is available via the API."},
        {"dimension": "Analysis-ready", "criterion": "Programmatic access",
         "description": "The ability to retrieve data using code-based "
                         "methods rather than manual browser-based "
                         "download.",
         "tier": "Analysis Ready", "met": True,
         "note": "Accessible via THREDDS, OPeNDAP, and cloud object "
                 "storage."},
        {"dimension": "Analysis-ready", "criterion": "Chunking and structure",
         "description": "How data are divided into discrete blocks for "
                         "storage and retrieval, and how files are "
                         "organized.",
         "tier": "AI-Optimized", "met": False,
         "note": "Chunk layout has not yet been optimized or documented "
                 "for cloud access patterns."},
        {"dimension": "Analysis-ready", "criterion": "Coordinate reference",
         "description": "The spatial and temporal location of data points "
                         "in a well-defined reference system.",
         "tier": "Analysis Ready", "met": True,
         "note": "CRS declared as EPSG:4326 with CF-compliant coordinate "
                 "variables."},
        {"dimension": "Analysis-ready", "criterion": "Interoperability",
         "description": "Whether data can be successfully loaded and used "
                         "with common open-source analysis and ML tools.",
         "tier": "AI-Optimized", "met": True,
         "note": "Validated with xarray and a PyTorch DataLoader in a "
                 "sample notebook."},

        # Findable and accessible
        {"dimension": "Findable and accessible", "criterion": "Discoverability",
         "description": "Whether a potential user can find the dataset "
                         "through standard search mechanisms.",
         "tier": "Acceptable", "met": True,
         "note": "Indexed in GDEX search and Globus Search."},
        {"dimension": "Findable and accessible", "criterion": "Persistent identification",
         "description": "A long-lasting reference, typically a DOI, that "
                         "remains stable even if the data's physical "
                         "location changes.",
         "tier": "Acceptable", "met": True,
         "note": "DOI registered via the GDEX DOI manager."},
        {"dimension": "Findable and accessible", "criterion": "Access conditions",
         "description": "The practical requirements a user must satisfy to "
                         "obtain the data.",
         "tier": "Acceptable", "met": True,
         "note": "Open access; no registration or approval required."},
        {"dimension": "Findable and accessible", "criterion": "Format interoperability",
         "description": "Whether data are in formats readable by a wide "
                         "range of tools without proprietary software.",
         "tier": "Analysis Ready", "met": True,
         "note": "NetCDF4/HDF5, readable by xarray, pandas, and GDAL."},

        # Clearly licensed
        {"dimension": "Clearly licensed", "criterion": "License presence",
         "description": "Whether terms of use or a recognized license are "
                         "explicitly stated and findable by users.",
         "tier": "Acceptable", "met": True,
         "note": "CC-BY 4.0 license linked on the Citation tab."},
        {"dimension": "Clearly licensed", "criterion": "Attribution requirements",
         "description": "How users must credit the data source when using "
                         "the data in publications, products, or derived "
                         "datasets.",
         "tier": "Analysis Ready", "met": True,
         "note": "Attribution statement included in the citation "
                 "guidance."},
        {"dimension": "Clearly licensed", "criterion": "Derivative work clarity",
         "description": "Whether the license makes it clear that data may "
                         "be used to create new products, train AI/ML "
                         "models, or be redistributed.",
         "tier": "AI-Optimized", "met": False,
         "note": "The license does not yet explicitly address AI/ML "
                 "training use."},
        {"dimension": "Clearly licensed", "criterion": "Restriction transparency",
         "description": "Whether any limitations on access or use are "
                         "documented and findable.",
         "tier": "AI-Optimized", "met": True,
         "note": "No access restrictions apply; stated explicitly in the "
                 "Data License section."},
    ],
}


def has_quality_checklist(dsid):
    """ Whether dsid has at least one quality assessment row, i.e. whether
    the Quality Checklist tab should be shown for it at all. """
    return dsid in FAKE_ASSESSMENTS


def build_checklist_context(dsid):
    """ Return the Quality Checklist tab context for dsid, or None if the
    dataset has not been assessed. """
    rows = FAKE_ASSESSMENTS.get(dsid)
    if rows is None:
        return None

    achieved_tier = None
    for tier in TIER_ORDER:
        cumulative = [r for r in rows
                      if TIER_ORDER.index(r["tier"]) <= TIER_ORDER.index(tier)]
        if cumulative and all(r["met"] for r in cumulative):
            achieved_tier = tier
        else:
            break

    dimensions = []
    for dimension_name in DIMENSION_ORDER:
        indicators = [r for r in rows if r["dimension"] == dimension_name]
        if indicators:
            dimensions.append({
                "name": dimension_name,
                "indicators": indicators,
                "met_count": sum(1 for r in indicators if r["met"]),
                "total_count": len(indicators),
            })

    return {
        "achieved_tier": achieved_tier,
        "tiers": TIER_ORDER,
        "dimensions": dimensions,
    }
