# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import json
import os

from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename

from agent_workflow_server.generated.models.agent_acp_descriptor import (
    AgentACPDescriptor,
)


class ACPDescriptorValidationException(Exception):
    pass


def _convert_descriptor_schema(schema_name, schema):
    return json.loads(
        json.dumps(schema).replace(
            "#/$defs/", f"#/components/schemas/{schema_name}/$defs/"
        )
    )


def _gen_oas_thread_runs(descriptor: AgentACPDescriptor, spec_dict):
    """Update thread-related paths and schemas"""
    if descriptor.specs.capabilities.threads:
        if descriptor.specs.thread_state:
            spec_dict["components"]["schemas"]["ThreadState"] = (
                _convert_descriptor_schema("ThreadState", descriptor.specs.thread_state)
            )
    else:
        # Remove thread-related paths and schemas
        thread_paths = [
            path for path in spec_dict["paths"].keys() if path.startswith("/threads")
        ]
        for path in thread_paths:
            del spec_dict["paths"][path]

        # Remove thread-related tags
        spec_dict["tags"] = [
            tag for tag in spec_dict["tags"] if tag["name"] != "Threads"
        ]


def _gen_oas_interrupts(descriptor: AgentACPDescriptor, spec_dict):
    """Update interrupt-related paths and schemas"""
    if not descriptor.specs.capabilities.interrupts:
        # Remove interrupt-related paths
        interrupt_paths = [
            path for path in spec_dict["paths"].keys() if "/interrupt" in path
        ]
        for path in interrupt_paths:
            del spec_dict["paths"][path]

        # Update RunOutput schema
        if "RunOutput" in spec_dict["components"]["schemas"]:
            output_schema = spec_dict["components"]["schemas"]["RunOutput"]
            if "oneOf" in output_schema:
                output_schema["oneOf"] = [
                    ref
                    for ref in output_schema["oneOf"]
                    if "interrupt" not in ref["$ref"]
                ]


def _gen_oas_streaming(descriptor: AgentACPDescriptor, spec_dict):
    """Update streaming-related paths and schemas"""
    if not descriptor.specs.capabilities.streaming:
        # Remove streaming paths
        if "/runs/{run_id}/stream" in spec_dict["paths"]:
            del spec_dict["paths"]["/runs/{run_id}/stream"]

        # Remove streaming from RunCreate
        if "RunCreate" in spec_dict["components"]["schemas"]:
            run_create = spec_dict["components"]["schemas"]["RunCreate"]
            if "properties" in run_create and "streaming" in run_create["properties"]:
                del run_create["properties"]["streaming"]


def _gen_oas_callback(descriptor: AgentACPDescriptor, spec_dict):
    # Manipulate the spec according to the callback capability flag in the descriptor
    if not descriptor.specs.capabilities.callbacks:
        # No streaming is supported. Removing callback option from RunCreate
        del spec_dict["components"]["schemas"]["RunCreate"]["properties"]["webhook"]


def generate_agent_oapi(descriptor: AgentACPDescriptor):
    spec_dict, base_uri = read_from_filename(
        os.getenv("ACP_SPEC_PATH", "acp-spec/openapi.json")
    )

    # If no exception is raised by validate(), the spec is valid.
    validate(spec_dict)

    spec_dict["info"]["title"] = (
        f"ACP Spec for {descriptor.metadata.ref.name}:{descriptor.metadata.ref.version}"
    )

    spec_dict["components"]["schemas"]["InputSchema"] = _convert_descriptor_schema(
        "InputSchema", descriptor.specs.input
    )
    spec_dict["components"]["schemas"]["OutputSchema"] = _convert_descriptor_schema(
        "OutputSchema", descriptor.specs.output
    )
    spec_dict["components"]["schemas"]["ConfigSchema"] = _convert_descriptor_schema(
        "ConfigSchema", descriptor.specs.config
    )

    _gen_oas_thread_runs(descriptor, spec_dict)
    _gen_oas_interrupts(descriptor, spec_dict)
    _gen_oas_streaming(descriptor, spec_dict)
    _gen_oas_callback(descriptor, spec_dict)

    validate(spec_dict)

    return spec_dict
