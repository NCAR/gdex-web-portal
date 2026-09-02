"""Portal views, split by section to mirror the templates/datasubmit/submission_portal/
layout (my_datasets/, submit/, budget_billing/, messages/, proposal_templates/).

Re-exported here so urls.py can keep doing `from . import views` /
`views.<name>` without caring which submodule a view actually lives in.
"""

from .budget_billing import data_submission_portal_budget
from .messages import data_submission_portal_messages
from .my_datasets import (
    data_submission_portal,
    data_submission_portal_files,
    data_submission_portal_metadata,
    data_submission_portal_set_view_mode,
    data_submission_portal_view,
)
from .proposal_templates import data_submission_portal_proposal_templates
from .submit import (
    data_submission_contributors,
    data_submission_gdex_next_steps,
    data_submission_welcome,
    data_submission_zenodo_next_steps,
    data_submission_zenodo_recommendation,
    gdex_submission_form_step,
    submission_advisor,
    submission_confirmation,
)

__all__ = [
    'data_submission_portal_budget',
    'data_submission_portal_messages',
    'data_submission_portal',
    'data_submission_portal_files',
    'data_submission_portal_metadata',
    'data_submission_portal_set_view_mode',
    'data_submission_portal_view',
    'data_submission_portal_proposal_templates',
    'data_submission_contributors',
    'data_submission_gdex_next_steps',
    'data_submission_welcome',
    'data_submission_zenodo_next_steps',
    'data_submission_zenodo_recommendation',
    'gdex_submission_form_step',
    'submission_advisor',
    'submission_confirmation',
]
