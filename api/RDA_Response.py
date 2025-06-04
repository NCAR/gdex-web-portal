import sys
import os
import json
from datetime import datetime



class RDA_Response:
    """ Standard RDA response object
    """


    def __init__(self, code=200, contact='rdahelp@ucar.edu', app_name=None):
        """ Creates default values.
        If ```error_code``` exists, treat response as error.
        """
        self.datetime = datetime.now()
        self.status = "ok"
        self.code = code
        self.messages = []
        self.data = {}
        self.app_name = app_name
        self.contact = contact
        if code != 200:
            self.add_error_message(code)

    def get_message(self, code):
        """Get message based on code."""
        message_dict = {
               111 : "No action option provided.",
               112 : "Option not defined.",
               113 : "Not enough arguments.",
               421 : "Request Index not found for email.",
               432 : "No requests for given email.",
               441 : "Request not yet complete.",
               442 : "Request is already set for purge.",
               460 : "Malformed dataset id or nonexisting dataset.",
               461 : "Purge error.",
               462 : "Couldn't complete purge.",
               463 : "JSON file not found or malformed JSON.",
               464 : "JSON not found.",
               465 : "JSON not found.",
               466 : "JSON not found.",
               467 : "JSON not found.",
               468 : "JSON not found.",
               469 : "JSON not found.",
               # Any error should be handled. This shouldn't happen.
               512 : "Unknown Server Error. Please contact rdahelp@ucar.edu",
               513 : "Problem connecting to database.",
               }
        if code not in message_dict:
            #return "Code " +code+ " not defined"
            return "Error: code " +str(code)
        return message_dict[code]

    def get_data(self):
        return self.data

    def add_data_members(self, key, value):
        self.data[key] = value

    def add_message(self, string):
        self.messages.append(string)
   
    def change_contact(self, contact):
        self.contact = contact

    def get_json(self):
        """Construct object"""
        now = datetime.now()
        obj = {}
        obj['status'] = self.status
        obj['http_response'] = self.code
        obj['error_messages'] = self.messages
        obj['data'] = self.data
        obj['contact'] = self.contact
        if self.app_name:
            obj['app_name'] = self.app_name
        #obj['request_start'] = self.datetime.isoformat()
        #obj['request_end'] = now.isoformat()
        #request_duration = str(get_time_duration(self.datetime, now)) + " seconds"
        #obj['request_duration'] = request_duration
        return obj

    def add_data(self, data):
        """Adds to the data key.
        This represents the actual returned data of the request.
        """
        try:
            self.data.update(data)
        except(ValueError) as e:
            print(e)
            self.data = data

    def add_error_message(self, code):
        """Sets message based on code"""

        self.status = 'error'
        if type(code) is str:
            self.code = 400
            message = code
        else:
            self.code = code
            message = self.get_message(code)
        self.add_message(message)


    def __str__(self):
        return json.dumps(self.get_json(), indent=4)

    __repr__ = __str__

def get_time_duration(start, end):
    """Get time in seconds between start and end"""
    diff = (end - start).total_seconds()
    return diff


if __name__ =='__main__':
    pass
