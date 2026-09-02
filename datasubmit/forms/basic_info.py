from django import forms

from .common import DATASET_SIZE_UNIT_CHOICES, PlaceholderSelect


class BasicInfoForm(forms.Form):
    dataset_title = forms.CharField(
        label='Dataset Title:',
        max_length=500,
        help_text="The complete name used to identify the dataset.",
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg"}),
    )

    # Only shown/required when the Advisor was skipped (recommendation
    # submissions) -- normally the Advisor's IntroForm already collected this.
    dataset_size = forms.IntegerField(
        label="Approximate Dataset Size:",
        widget=forms.NumberInput(attrs={"class": "form-control form-control-lg"}),
        help_text="This is an approximation and will be verified later in the process.",
        required=False,
    )

    dataset_size_units = forms.ChoiceField(
        label="Units",
        choices=DATASET_SIZE_UNIT_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-select form-select-lg"}),
        required=False,
    )

    dataset_abstract = forms.CharField(
        label="Abstract/Describe Your Data:",
        max_length=5000,
        help_text="A summary highlighting the key characteristics/features of the dataset. "
        "The abstract should be similar to a journal publication abstract in order to provide"
        " sufficient information to inform users if this might be a suitable resource for them.",
        widget=forms.Textarea(attrs={"class": "form-control form-control-lg"}),
    )

    dataset_details = forms.CharField(
        label="Additional Dataset Details:",
        max_length=5000,
        help_text="An extended explanation of the dataset's details, such as background information, "
        "objectives, and methods. The description should provide basic documentation that frames the "
        "context for the dataset. If a more complete description is available in a separate document "
        "format, please indicate the availability of the document in the field. If the document is "
        "accessible via a URL, please provide the URL in the field.",
        widget=forms.Textarea(attrs={"class": "form-control form-control-lg"}),
        required=False,
    )

    def __init__(self, *args, is_recommendation=False, **kwargs):
        super().__init__(*args, **kwargs)
        if is_recommendation:
            self.fields['dataset_size'].required = True
            self.fields['dataset_size_units'].required = True
        else:
            # The Advisor already collected this -- don't ask twice.
            del self.fields['dataset_size']
            del self.fields['dataset_size_units']

        # Django auto-adds a hard HTML `maxlength` for CharFields, which silently truncates
        # typed/pasted text at the limit. Swap it for a data-attribute so the counter can warn
        # the user instead, letting them see (and still submit) the full text they entered.
        for name in ('dataset_title', 'dataset_abstract', 'dataset_details'):
            field = self.fields[name]
            field.widget.attrs['data-maxlength'] = field.max_length
            del field.widget.attrs['maxlength']
