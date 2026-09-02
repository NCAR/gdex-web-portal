from django import forms

from .common import DATASET_SIZE_UNIT_CHOICES, YES_NO_CHOICES, PlaceholderSelect

HPC_ACCESS_CHOICES = [
    ('', 'Select an option'),
    (True, "Yes, I need HPC access"),
    (False, "No, I don't need HPC access"),
]

SUBMISSION_CONTENT_CHOICES = [
    ('', 'Select an option'),
    ('dataset', 'Dataset'),
    ('software_only', 'Software only'),
    ('software_and_dataset', 'Software + Dataset'),
]


class IntroForm(forms.Form):
    dataset_size = forms.IntegerField(
        label="Approximate Dataset Size:",
        widget=forms.NumberInput(attrs={"class": "form-control form-control-lg"}),
        help_text="This is an approximation and will be verified later in the process.",
    )

    dataset_size_units = forms.ChoiceField(
        label="Units",
        choices=DATASET_SIZE_UNIT_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
    )

    cif_fare_contributors = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
        help_text=(
            ' To check, review your NSF award documentation or search your award in the NSF '
            'Award Search database. '
            '<a href="https://www.nsf.gov/funding/opportunities/fare-facilities-atmospheric-research-education" '
            'target="_blank" rel="noopener" '
            'aria-label="Learn more about the FARE program (opens in a new tab)">'
            '<i class="fas fa-external-link-alt" aria-hidden="true"></i></a>'

        ),
        label= "Is this project part of, or funded by, the NSF Community Instrument Facility (CIF) or Facilities for Atmospheric Research and Education (FARE) programs?"
    )

    hpc_access = forms.ChoiceField(
        choices=HPC_ACCESS_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
        help_text=(
            ' Answer Yes if you expect to access, analyze, process, or visualize the archived '
            'data using NCAR\'s HPC resources. '
            '<a href="https://arc.ucar.edu/resources" target="_blank" rel="noopener" '
            'aria-label="Learn more about NCAR HPC Resources (opens in a new tab)">'
            '<i class="fas fa-external-link-alt" aria-hidden="true"></i></a>'
            '<br> This allows the archived data to be available '
            'directly on NCAR\'s computing systems without requiring you to download or transfer '
            'it elsewhere. Answer No if you do not need continued access to the archived data '
            'through NCAR\'s HPCs. '

        ),
        label= "Will you need access to the archived data via NCAR's HPCs?"
    )


    submission_content = forms.ChoiceField(
        choices=SUBMISSION_CONTENT_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
        label= "Are you submitting a dataset, software, or both?"
    )

    is_ncar_employee = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
        label= "Are you an NCAR/UCAR employee?"
    )


class ZenodoChoiceForm(forms.Form):
    continue_with_gdex = forms.ChoiceField(
        choices = YES_NO_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-control form-control-lg"}),
        label= "Would you still like to submit this dataset to GDEX?"
    )
