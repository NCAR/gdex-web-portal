from django import forms
from django.core.validators import RegexValidator

from .common import YES_NO_CHOICES, PlaceholderSelect

orcid_validator = RegexValidator(
    regex=r'^\d{4}-\d{4}-\d{4}-\d{4}$',
    message="Enter a valid ORCID iD in the format 0000-0000-0000-0000.",
)


class ContributorsMetaForm(forms.Form):
    submitted_by_organization = forms.ChoiceField(
        choices = YES_NO_CHOICES,
        widget=PlaceholderSelect(attrs={"class": "form-control form-control-lg"}),
        label= "Is this dataset being submitted by an institution or organization, rather than by a person or people?"
    )


class AuthorForm(forms.Form):
    last_name = forms.CharField(
        label="Last Name",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "Doe"}),
    )

    first_name = forms.CharField(
        label="First Name",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "Jane"}),
    )

    middle_name = forms.CharField(
        label="Middle Name",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "Rose"}),
    )

    orcid_id = forms.CharField(
        label="ORCID iD",
        max_length=19,
        required=False,
        validators=[orcid_validator],
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "0000-0000-0000-0000",}),
    )

    affiliation = forms.CharField(
        label="Institution/Organization",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "NSF National Center for Atmospheric Research (NCAR)"}),
    )

    def __init__(self, *args, is_organization=False, **kwargs):
        self.is_organization = is_organization
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.is_organization:
            if not cleaned_data.get('affiliation'):
                self.add_error('affiliation', "Institution/Organization is required.")
        else:
            if not cleaned_data.get('first_name'):
                self.add_error('first_name', "First name is required.")
            if not cleaned_data.get('last_name'):
                self.add_error('last_name', "Last name is required.")
        return cleaned_data


class _AuthorBaseFormSet(forms.BaseFormSet):
    """Renders the ORDER/DELETE management fields as hidden inputs, driven entirely by JS."""

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if self.can_order:
            form.fields['ORDER'].widget = forms.HiddenInput()
        if self.can_delete:
            form.fields['DELETE'].widget = forms.HiddenInput()


AuthorFormSet = forms.formset_factory(
    AuthorForm,
    formset=_AuthorBaseFormSet,
    extra=0,
    can_delete=True,
    can_order=True,
    min_num=1,
    validate_min=True,
)
