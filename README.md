# GDEX Web Portal

This project contains the Python Django framework supporting the [NSF NCAR Geoscience Data Exchange (GDEX)](https://gdex.ucar.edu) data portal.

## Description of apps

### api
    This contains code to support the api
    
    - `common.py` 
        - Mostly a database interface and helper functions
    - `get_actions.py`
        - Entry point for HTTPS GET requests
    - `post_actions.py`
        - Entry point for HTTPS POST requests
    - `others`
        - default response template
