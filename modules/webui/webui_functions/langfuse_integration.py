"""
title: Langfuse Filter Pipeline
author: open-webui
license: MIT
description: Adds Langfuse integration with query logging and prompt version control
requirements: langfuse
"""

from typing import List, Optional
import os
import json

from pydantic import BaseModel
from langfuse import Langfuse
from langfuse.api.resources.commons.errors.unauthorized_error import UnauthorizedError
from langfuse.client import StatefulGenerationClient, StatefulTraceClient


def get_last_assistant_message_obj(messages: List[dict]) -> dict:
    for message in reversed(messages):
        if message["role"] == "assistant":
            return message
    return {}


class Filter:
    class Valves(BaseModel):
        pipelines: List[str] = ['*']
        priority: int = 0
        secret_key: str = os.getenv('LANGFUSE_SECRET_KEY', 'sk-lf-KEYS')
        public_key: str = os.getenv('LANGFUSE_PUBLIC_KEY', 'pk-lf-SET')
        host: str = os.getenv('LANGFUSE_HOST', 'http://langfuse:7000')
        sys_prompt_name: str = os.getenv('SYS_PROMPT_NAME', 'Webui_System_Prompt')
        enable_sys_prompt: bool = False
        sys_model_filter: List[str] = ['*']

    def __init__(self):
        self.type = "filter"
        self.name = "Langfuse Filter"
        self.valves = self.Valves()
        self.langfuse = None
        self.chat_generations = {}
        self.set_langfuse()

    def set_langfuse(self):
        try:
            self.langfuse = Langfuse(
                secret_key=self.valves.secret_key,
                public_key=self.valves.public_key,
                host=self.valves.host,
                debug=False,
            )
            self.langfuse.auth_check()
        except UnauthorizedError:
            print(
                "Langfuse credentials incorrect. Please re-enter your Langfuse credentials in the pipeline settings."
            )
        except Exception as e:
            print(
                f"Langfuse error: {e} Please re-enter your Langfuse credentials in the pipeline settings."
            )

    def _get_langfuse_prompt(self):
        langfuse_prompt = None
        try:
            langfuse_prompt = self.langfuse.get_prompt(self.valves.sys_prompt_name)
            if not langfuse_prompt:
                raise RuntimeError('No prompt found')
        except Exception as ex:
            # Assume there is no system prompt in the event of an error
            print(f"Failed to fetch prompt: {ex}")
            return None
        return langfuse_prompt

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        metadata = body.get('metadata', {})
        print(json.dumps(metadata, indent=2))
        if 'task' in metadata or 'chat_id' not in metadata:
            return body # Ignore non-chat messages

        langfuse_prompt = None
        if (
            body['messages'][0]['role'] != 'system'
            and self.valves.enable_sys_prompt
            and (
                '*' in self.valves.sys_model_filter
                or body['model'] in self.valves.sys_model_filter
            )
        ):
            langfuse_prompt = self._get_langfuse_prompt()
            body['messages'].insert(0, {'role': 'system', 'content': langfuse_prompt.prompt})

        trace = self.langfuse.trace(
            name=f'filter:{__name__}',
            id=metadata['message_id'],
            input=body,
            user_id=__user__['email'],
            metadata={
                'user_name': __user__['name'],
                'user_id': __user__['id'],
                **metadata,
            },
            session_id=metadata['chat_id'],
        )

        generation = trace.generation(
            id=metadata['message_id'],
            model=body['model'],
            input=body['messages'],
            metadata={'interface': 'open-webui'},
            prompt=langfuse_prompt,
        )

        self.chat_generations[body['metadata']['chat_id']] = (trace, generation)
        return body

    def outlet(self, body: dict) -> dict:
        # For some wacky reason, the webui adds a `chat_id` field to the body
        # in outlets even though it is added in the "metadata" for inlets
        langfuse_ids = self.chat_generations.pop(body['chat_id'], None)
        if not langfuse_ids:
            return body

        trace: StatefulTraceClient = langfuse_ids[0]
        generation: StatefulGenerationClient = langfuse_ids[1]

        model_response = get_last_assistant_message_obj(body['messages'])
        generation.end(
            output=model_response,
            usage=model_response.get('usage', None),
        )
        trace.update(output=model_response)
        return body
