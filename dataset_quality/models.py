from django.db import models

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class QualityTier(models.Model):
    """ A tier in the dataset quality checklist (e.g. Acceptable, Analysis
    Ready, AI-Optimized). Tiers are cumulative: a dataset achieves a tier
    only when every indicator assigned to that tier or a lower-ordered tier
    is met. """

    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(
        unique=True,
        help_text="Rank of this tier from lowest (0) to highest bar",
    )

    panels = [
        MultiFieldPanel([
            FieldPanel("name"),
            FieldPanel("order"),
        ])
    ]

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


@register_snippet
class QualityDimension(models.Model):
    """ A grouping of related quality criteria (e.g. Prepared and
    Consistent, Well-documented). """

    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    panels = [
        MultiFieldPanel([
            FieldPanel("name"),
            FieldPanel("order"),
        ])
    ]

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


@register_snippet
class QualityIndicator(models.Model):
    """ A single checklist criterion belonging to a dimension and assigned
    to the tier at which it becomes a requirement. Reference data, shared
    across all datasets. """

    dimension = models.ForeignKey(
        QualityDimension, on_delete=models.PROTECT,
        related_name="indicators",
    )
    tier = models.ForeignKey(
        QualityTier, on_delete=models.PROTECT,
        related_name="indicators",
    )
    criterion = models.CharField(
        max_length=255,
        help_text="Short name of the criterion, e.g. 'Missing values'",
    )
    description = models.TextField(
        help_text="Full indicator description shown to users",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within the dimension",
    )

    panels = [
        MultiFieldPanel([
            FieldPanel("dimension"),
            FieldPanel("tier"),
            FieldPanel("criterion"),
            FieldPanel("description"),
            FieldPanel("order"),
        ])
    ]

    class Meta:
        ordering = ["dimension__order", "order"]

    def __str__(self):
        return f"{self.criterion} ({self.tier})"


@register_snippet
class DatasetQualityAssessment(models.Model):
    """ Whether a specific dataset satisfies a specific QualityIndicator.
    Rows are created as datasets are assessed; a dataset with no rows has
    not been assessed and should not show a Quality Checklist tab. Absence
    of a row for a given indicator is treated the same as "not met" when
    computing a dataset's achieved tier. """

    SOURCE_CHOICES = [
        ("manual", "Manual"),
        ("automated", "Automated"),
    ]

    dsid = models.CharField(max_length=9, db_index=True)
    indicator = models.ForeignKey(
        QualityIndicator, on_delete=models.CASCADE,
        related_name="assessments",
    )
    met = models.BooleanField(default=False)
    note = models.TextField(blank=True, default="")
    source = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, default="manual",
    )
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        MultiFieldPanel([
            FieldPanel("dsid"),
            FieldPanel("indicator"),
            FieldPanel("met"),
            FieldPanel("note"),
            FieldPanel("source"),
        ])
    ]

    class Meta:
        unique_together = [("dsid", "indicator")]

    def __str__(self):
        return f"{self.dsid} - {self.indicator.criterion}"
