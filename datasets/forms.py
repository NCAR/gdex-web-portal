from django import forms
import re
from api.common import init_connection_new

def validate_dsid(value):
    if not re.match(r'^[a-z]{1}[0-9]{6}$', value):
        raise forms.ValidationError("Dataset ID format must be 'd123456'.")

class DatasetRequestForm(forms.Form):
    rtype = forms.ChoiceField(required=True, label="rtype", help_text="Request Type", choices=[("S", "S - Subset Data"), ("T", "T - Subset/Format-Conversion Data")])
    dsid = forms.CharField(max_length=7, required=True, label="dsid", help_text="Dataset ID", validators=[validate_dsid])
    gindex = forms.TypedChoiceField(required=True, coerce=int, empty_value=None, choices=None, label="gindex", help_text="Group Index from dsrqst control (default 0)")
    email = forms.EmailField(required=False, initial=None, label="email", help_text="User Email Address (retrieved from user login if not provided)")
    rstat = forms.ChoiceField(choices=[("Q", "Q - Queued"), ("W", "W - Wait")], initial="Q",required=False, label="rstat", help_text="Request Status")
    sflag = forms.ChoiceField(required=False, choices=[(0, "0 - Default"), (1, "1 - Variable"), (2, "2 - Temporal"), (4, "4 - Spatial")], label="sflag", help_text="Subset Flag")
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
        
    def get_gindex_choices(self):
        conn, cursor = init_connection_new()
        cursor.execute("SELECT gindex FROM rcrqst WHERE dsid = %s AND (rqsttype = 'S' OR rqsttype = 'T')", (self.initial.get('dsid', None),))
        choices = cursor.fetchall()
        cursor.close()
        conn.close()
        if not choices:
            return [(0, "0 - Default group index")]
        else:
            return [(choice[0], f"{choice[0]}") for choice in choices]
