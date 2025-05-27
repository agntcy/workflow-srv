# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio

from llama_index.core.workflow import (
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)


class JokeEvent(Event):
    joke: str


class JokeFlow(Workflow):
    @step
    async def generate_joke(self, ev: StartEvent) -> JokeEvent:
        topic = ev.topic

        response = "this is a joke about " + topic
        asyncio.sleep(1)
        return JokeEvent(joke=str(response))

    @step
    async def critique_joke(self, ev: JokeEvent) -> StopEvent:
        joke = ev.joke

        response = "this is a critique of the joke: " + joke
        return StopEvent(result=str(response))


async def main():
    w = JokeFlow(timeout=60, verbose=False)
    result = await w.run(topic="pirates")
    print(str(result))


if __name__ == "__main__":
    asyncio.run(main())
