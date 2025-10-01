#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 17 11:59:08 2025

@author: augustin
"""

from datetime import datetime
import json

current_date = datetime.today().strftime('%Y-%m-%d')


# =============================================================================
# Open latest_changelog.md and put it in a list
# =============================================================================
with open("docs/latest_changelog.md", "r") as latest_changelog:
    latest_list = latest_changelog.readlines()
    latest_changelog.close()

# =============================================================================
# Read and Update codemete
# =============================================================================
with open('codemeta.json', 'r') as file:
    data = json.load(file)

data["releaseNotes"] = ''.join(latest_list)
data["dateModified"] = current_date

# =============================================================================
# Write new file
# =============================================================================
with open('codemeta.json', mode="w", encoding="utf-8") as write_file:
    json.dump(data, write_file, indent=4)
