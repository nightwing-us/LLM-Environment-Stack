"""
title: LiteLLM Set End User
description: Allows LiteLLM to track end user costs
version: 0.1
"""

from pydantic import BaseModel, Field


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0, description="Priority level for the filter operations."
        )

    def __init__(self):
        self.valves = self.Valves()
        pass

    def inlet(self, body: dict, __user__: dict) -> dict:
        body['user'] = __user__.get('email', None)
        body['extra_body']['litellm_session_id'] = body['metadata']['chat_id']
        return body

    def outlet(self, body: dict) -> dict:
        return body
