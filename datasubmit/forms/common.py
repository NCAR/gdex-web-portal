from django import forms

YES_NO_CHOICES = [
        ('', 'Select an option'),
        (True, 'Yes'),
        (False, 'No'),
    ]

# 1024-based (binary) multipliers, matching typical HPC/archive file-size conventions.
DATASET_SIZE_UNIT_TO_MB = {
    'MB': 1,
    'GB': 1024,
    'TB': 1024 ** 2,
    'PB': 1024 ** 3,
}
DATASET_SIZE_UNIT_CHOICES = [('', 'Select a unit')] + [(unit, unit) for unit in DATASET_SIZE_UNIT_TO_MB]


def convert_dataset_size_to_mb(size, unit):
    return size * DATASET_SIZE_UNIT_TO_MB[unit]


def mark_invalid_fields(form):
    """Called from views/ after a failed form.is_valid(). Adds the visual
    is-invalid border sighted users already got, plus aria-invalid and
    aria-describedby pointing at that field's error container -- so screen
    readers get the same "this field failed" signal instead of just a color
    change. Templates must render the matching error container with
    id="{{ field.auto_id }}_error" for the describedby link to resolve."""
    for field_name in form.errors:
        field = form[field_name]
        widget = field.field.widget
        widget.attrs['class'] = (widget.attrs.get('class', '') + ' is-invalid').strip()
        widget.attrs['aria-invalid'] = 'true'
        widget.attrs['aria-describedby'] = f'{field.auto_id}_error'


class PlaceholderSelect(forms.Select):
    """A <select> whose blank choice renders disabled, like a text input's placeholder."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value == '':
            option['attrs']['disabled'] = True
        return option
