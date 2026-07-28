from django import forms


class PoliciesForm(forms.Form):
    def __init__(self, *args, is_ncar_employee=None, **kwargs):
        self.is_ncar_employee = is_ncar_employee
        super().__init__(*args, **kwargs)

    data_policy_agreement = forms.BooleanField(
        required=True,
        label="I agree to the above terms and conditions.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    data_deposit_agreement = forms.BooleanField(
        required=False,
        label="I agree to the data deposit agreement below",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if self.is_ncar_employee == 'False' and not cleaned_data.get('data_deposit_agreement'):
            self.add_error(
                'data_deposit_agreement',
                "Non-UCAR contributors must agree to the Data Deposit Agreement.",
            )
        return cleaned_data
