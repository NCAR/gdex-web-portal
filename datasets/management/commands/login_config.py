from django.core.management.base import BaseCommand
import sys
import configparser

from wagtail.models import Page
from datasets.models import DatasetsPage
from dataset_description.models import DatasetDescriptionPage
from dataset_citation.models import DatasetCitationPage


valid_actions = [
    "set",
    "unset",
]

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('action', type=str, help="action to take: set|unset")
        parser.add_argument('section', type=str, help="section of configuration to modify")
        parser.add_argument('setting', type=str, help="setting to modify")
        parser.add_argument('--value', type=str, help="value of setting - required if being set")

    def handle(self, *args, **options):
        action = options['action']
        if not action in valid_actions:
            sys.exit("Error: bad action")

        section = options['section']
        config = configparser.ConfigParser(allow_no_value=True)
        config.optionxform = str
        config_file = "/usr/local/rdaweb/login/config.ini"
        config.read(config_file)
        setting = options['setting']
        if action == "set":
            if options['value'] is None:
                sys.exit("Error: no value provided for setting")

            value = None if len(options['value']) == 0 else options['value']

            if not section in config:
                config[section] = {}

            config.set(section, setting, value)

        elif action == "unset":
            config.remove_option(section, setting)
            if len(config[section]) == 0:
                config.remove_section(section)

        # output the new configuration
        with open(config_file, "w") as file:
            config.write(file)
            file.flush()
            file.close()

        print("Success: configuration updated")
