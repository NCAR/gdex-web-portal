from django import forms
import re
from api.common import init_connection_new
from facbrowse.utils import get_groups


# ---------------------------------------------------------------------------
# BUFR upper-air subset form (d351000)
# ---------------------------------------------------------------------------

class BUFRD351SubsetForm(forms.Form):

    SPATIAL_CHOICES = [
        ('-1', ''),
        ('0', 'Select latitude/longitude region via map'),
        ('1', 'Select location by station ID'),
    ]

    RECTYPE_CHOICES = [
        ('ADPUPA',       'ADPUPA — Rawinsonde, PIBAL, fixed/mobile land and ship'),
        ('AIRCAR AIRCFT', 'AIRCAR AIRCFT — AIREP, PIREP, ACARS, (T)AMDAR, etc.'),
        ('SATWND',       'SATWND — Satellite Derived Winds'),
    ]

    PARM_CHOICES = [
        ('PRLC', 'PRLC — Pressure'),
        ('PSAL', 'PSAL — Pressure altitude relative to mean sea level pressure'),
        ('GP10', 'GP10 — Geopotential'),
        ('GP07', 'GP07 — Geopotential'),
        ('FLVL', 'FLVL — Flight level'),
        ('WDIR', 'WDIR — Wind direction'),
        ('WSPD', 'WSPD — Wind speed'),
        ('TMDB', 'TMDB — Temperature/dry bulb temperature'),
        ('TMDP', 'TMDP — Dew-point temperature'),
        ('REHU', 'REHU — Relative humidity'),
    ]

    COMPRESSION_CHOICES = [
        ('gz', '.gz (Gzip)'),
        ('None', 'No compression'),
    ]

    # ------------------------------------------------------------------
    # Hidden fields – set/modified by JavaScript during form interaction
    # ------------------------------------------------------------------
    dsid           = forms.CharField(widget=forms.HiddenInput, required=False)
    gindex         = forms.IntegerField(widget=forms.HiddenInput, required=False, initial=1)
    rtype          = forms.CharField(widget=forms.HiddenInput, required=False, initial='S')
    mapdisplayed   = forms.IntegerField(widget=forms.HiddenInput, required=False, initial=0)
    latlondisplayed = forms.IntegerField(widget=forms.HiddenInput, required=False, initial=0)
    stationdisplayed = forms.IntegerField(widget=forms.HiddenInput, required=False, initial=0)
    tlat           = forms.CharField(widget=forms.HiddenInput, required=False)
    blat           = forms.CharField(widget=forms.HiddenInput, required=False)
    llon           = forms.CharField(widget=forms.HiddenInput, required=False)
    rlon           = forms.CharField(widget=forms.HiddenInput, required=False)

    # ------------------------------------------------------------------
    # Temporal range
    # ------------------------------------------------------------------
    startDate = forms.DateField(
        required=False,
        label='Start Date',
        input_formats=['%Y-%m-%d'],
        widget=forms.TextInput(attrs={
            'placeholder': 'YYYY-MM-DD',
            'size': '10',
            'maxlength': '10',
        }),
    )
    endDate = forms.DateField(
        required=False,
        label='End Date',
        input_formats=['%Y-%m-%d'],
        widget=forms.TextInput(attrs={
            'placeholder': 'YYYY-MM-DD',
            'size': '10',
            'maxlength': '10',
        }),
    )

    # ------------------------------------------------------------------
    # Spatial range
    # ------------------------------------------------------------------
    gridSelection = forms.ChoiceField(
        required=False,
        choices=SPATIAL_CHOICES,
        label='Spatial Subset Preference',
        widget=forms.Select(attrs={
            'class': 'custom-select',
            'onchange': 'displayGridSelection(document.form.gridSelection.value)',
        }),
    )

    # ------------------------------------------------------------------
    # Station IDs (comma-separated list of 5-digit WMO numbers)
    # ------------------------------------------------------------------
    station0  = forms.CharField(required=False, max_length=5, label='Station 1',  widget=forms.Textarea(attrs={'class': 'form-control stns', 'rows': '4', 'tabindex': '1'}))

    # ------------------------------------------------------------------
    # Record types
    # ------------------------------------------------------------------
    rectypes = forms.MultipleChoiceField(
        required=False,
        choices=RECTYPE_CHOICES,
        label='Record Types',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )

    # ------------------------------------------------------------------
    # Parameters
    # ------------------------------------------------------------------
    parms = forms.MultipleChoiceField(
        required=False,
        choices=PARM_CHOICES,
        label='Parameters',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )

    # ------------------------------------------------------------------
    # File compression
    # ------------------------------------------------------------------
    compression = forms.ChoiceField(
        required=False,
        choices=COMPRESSION_CHOICES,
        label='File Compression',
        initial='gz',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('startDate')
        end   = cleaned.get('endDate')
        if start and end and start > end:
            raise forms.ValidationError('Start date must not be later than end date.')
        return cleaned

def validate_dsid(value):
    if not re.match(r'^[a-z]{1}[0-9]{6}$', value):
        raise forms.ValidationError("Dataset ID format must be 'd123456'.")

class DatasetRequestForm(forms.Form):
    rtype = forms.ChoiceField(required=True, label="rtype", help_text="Request Type", choices=[("S", "S - Subset Data"), ("T", "T - Subset/Format-Conversion Data")])
    dsid = forms.CharField(max_length=7, required=True, label="dsid", help_text="Dataset ID", validators=[validate_dsid])
    gindex = forms.TypedChoiceField(required=True, coerce=int, empty_value=None, choices=None, label="gindex", help_text="Group Index from dsrqst control (default 0)")
    email = forms.EmailField(required=False, initial=None, label="email", help_text="User Email Address (retrieved from user login if not provided)")
    rstat = forms.ChoiceField(choices=[("Q", "Q - Queued"), ("W", "W - Wait")], initial="Q",required=False, label="rstat", help_text="Request Status")
    sflag = forms.ChoiceField(required=False, choices=None, label="sflag", help_text="Bitwise Subset Flag")
    tflag = forms.ChoiceField(choices=[("Y", "Yes"), ("N", "No")], required=False, initial="N", label="tflag", help_text="Tar Flag")
    dfmt = forms.CharField(max_length=10, required=False, label="dfmt", help_text="Data Format")
    afmt = forms.CharField(max_length=10, required=False, label="afmt", help_text="Archive Format (Zip/Tar/compress, GZ, TAR.GZ, etc.)")
    size_request = forms.IntegerField(required=False, label="size_request", help_text="Requested Size (Bytes)")
    size_input = forms.IntegerField(required=False, label="size_input", help_text="Input Size (Bytes)")
    fcount = forms.IntegerField(required=False, label="fcount", help_text="File Count")
    ptlimit = forms.IntegerField(required=False, label="ptlimit", help_text="Max file count in each partition")
    ptsize = forms.IntegerField(required=False, label="ptsize", help_text="Max data size for each request partition (Bytes)")
    command = forms.CharField(max_length=256, required=False, label="command", help_text="Execution Command for processing requested files")
    fromflag = forms.CharField(widget=forms.HiddenInput, required=False, max_length=1, initial="W", label="fromflag", help_text="From Flag (indicates request is from web interface)")
    location = forms.CharField(widget=forms.HiddenInput, required=False, initial="web", label="location", help_text="Request output directory path, if different from the default path.")
    rinfo = forms.CharField(required=True, label="rinfo", help_text="Request information (query parameter string)")
    rnote = forms.CharField(widget=forms.Textarea, required=False, label="rnote", help_text="Request Note (readable version of rinfo)")

    def __init__(self, *args, **kwargs):
        super(DatasetRequestForm, self).__init__(*args, **kwargs)
        self.fields['gindex'].choices = self.get_gindex_choices()
        self.fields['sflag'].choices = self.get_sflag_choices()
        
    def get_gindex_choices(self):
        """ Provides choices for the group index field. """
        groups = get_groups(self.initial.get('dsid', None))
        if not groups:
            return [(0, "0 - Default group index")]
        else:
            choices = [(0, "0 - Default group index")]
            for group in groups:
                index = group['gindex']
                if 'title' not in group or not group['title']:
                    title = 'No Title'
                else:
                    title = group['title']
                choices.append((index, f"{index} - {title}"))
            return choices

    def get_sflag_choices(self):
        """ Provides choices for the bitwise subset flag field. """
        return [
            (0, "0 - Default"), 
            (1, "1 - Variable"), 
            (2, "2 - Temporal"), 
            (3, "3 - Variable and Temporal"), 
            (4, "4 - Spatial"),
            (5, "5 - Variable and Spatial"), 
            (6, "6 - Temporal and Spatial"), 
            (7, "7 - Variable, Temporal, and Spatial")
        ]