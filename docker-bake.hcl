// SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
// SPDX-License-Identifier: Apache-2.0


# Documentation available at: https://docs.docker.com/build/bake/

# Docker build args
variable "IMAGE_REPO" {default = ""}
variable "IMAGE_TAG" {default = "v0.0.0-dev"}

function "get_tag" {
  params = [tags, name]
  result = coalescelist(tags, ["${IMAGE_REPO}/${name}:${IMAGE_TAG}"])
}

group "default" {
  targets = ["workflowserver"]
}

group "workflowserver" {
  targets = [
    "workflowserver",
  ]
}

target "_common" {
  output = [
    "type=image",
  ]
  platforms = [
    "linux/arm64",
    "linux/amd64",
  ]
}

target "docker-metadata-action" {
  tags = []
}

target "workflowserver-dev" {
  context = "."
  dockerfile = "assets/workflowserver.Dockerfile"
  tags = [
    "workflowserver:latest",
    ]
}

target "workflowserver" {
  tags = get_tag(target.docker-metadata-action.tags, "${target.workflowserver.name}")
  inherits = [
    "workflowserver-dev",
    "_common",
    "docker-metadata-action",
  ]
}