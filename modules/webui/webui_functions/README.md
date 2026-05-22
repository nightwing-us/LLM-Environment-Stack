# Default Pipelines
All Python files in this directory will automatically be loaded by the Pipelines
service to act as plugins to open-webui. Each one performs some action on the
query of the user and/or the response of the model before being handed back to
the user.

## Open-Webui Langfuse Integration for Pipelines
This plugin is designed to log user interactions and model responses in
open-webui via the Langfuse service. Any time the user queries the model in
open-webui, their prompt, user ID, and signup email will be logged to Langfuse
as a separate trace (a log for single inputs/outputs) in the same session (log
for associated traces; eg. multiple turns in a chat). Upon completion of the
model's response, it will also be logged to the same trace.

In addition to logging user interactions, there is also an optional method of
setting up system prompts to be associated with these queries. This allows
administrators monitor model responses for regressions and role back the system
prompt to a previous version should a regression occur.
