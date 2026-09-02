"""Submission-wizard forms, split by wizard step to mirror
views/submit.py's STEP_SLUGS (advisor -> basic_info -> contributors ->
access_info -> policies).

Re-exported here so views/ can keep doing `from ..forms import ...`
without caring which submodule a form actually lives in.
"""

from .access_info import (
    ACCESS_METHOD_CHOICES,
    ACCESS_METHOD_DETECTION_ORDER,
    ACCESS_METHOD_INFO,
    AccessInfoForm,
    detect_access_method,
)
from .advisor import HPC_ACCESS_CHOICES, SUBMISSION_CONTENT_CHOICES, IntroForm, ZenodoChoiceForm
from .basic_info import BasicInfoForm
from .common import (
    DATASET_SIZE_UNIT_CHOICES,
    DATASET_SIZE_UNIT_TO_MB,
    SUBMISSION_TYPE_CHOICES,
    YES_NO_CHOICES,
    PlaceholderSelect,
    convert_dataset_size_to_mb,
    mark_invalid_fields,
)
from .contributors import AuthorForm, AuthorFormSet, ContributorsMetaForm, orcid_validator
from .policies import PoliciesForm

__all__ = [
    'ACCESS_METHOD_CHOICES',
    'ACCESS_METHOD_DETECTION_ORDER',
    'ACCESS_METHOD_INFO',
    'AccessInfoForm',
    'detect_access_method',
    'HPC_ACCESS_CHOICES',
    'SUBMISSION_CONTENT_CHOICES',
    'IntroForm',
    'ZenodoChoiceForm',
    'BasicInfoForm',
    'DATASET_SIZE_UNIT_CHOICES',
    'DATASET_SIZE_UNIT_TO_MB',
    'SUBMISSION_TYPE_CHOICES',
    'YES_NO_CHOICES',
    'PlaceholderSelect',
    'convert_dataset_size_to_mb',
    'mark_invalid_fields',
    'AuthorForm',
    'AuthorFormSet',
    'ContributorsMetaForm',
    'orcid_validator',
    'PoliciesForm',
]
