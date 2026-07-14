# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from unittest.mock import patch

import google.auth
import google.auth.exceptions
from dotenv import load_dotenv

# Load local development environment variables (.env) before executing tests
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

try:
    google.auth.default()
except google.auth.exceptions.DefaultCredentialsError:
    # Globally mock GCP credentials for local test runners when ADC is missing
    from google.auth.credentials import AnonymousCredentials

    patcher = patch(
        "google.auth.default",
        return_value=(AnonymousCredentials(), "rm-fde-training-sandbox-122462"),
    )
    patcher.start()
