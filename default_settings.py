# -*- coding: utf-8 -*-
import os
from os.path import dirname, join

SECRET_KEY = os.urandom(16)
# configure file based session
SESSION_TYPE = "filesystem"
SESSION_FILE_DIR = join(dirname(__file__), "cache")

# configure flask app for local development
ENV = "development"
