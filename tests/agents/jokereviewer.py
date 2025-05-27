# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
import asyncio

from dotenv import find_dotenv, load_dotenv
from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

load_dotenv(dotenv_path=find_dotenv(usecwd=True))


class SecondEvent(Event):
    joke: str
    ai_answer: str


class FirstInterruptEvent(Event):
    joke: str
    first_question: str
    needs_answer: bool


class InterruptResponseEvent(Event):
    answer: str


class JokeEvent(Event):
    joke: str


class JokeReviewer(Workflow):
    @step
    async def generate_joke(self, ev: StartEvent) -> JokeEvent:
        topic = ev.topic
        response = "this is a joke about " + topic
        await asyncio.sleep(1)
        return JokeEvent(joke=str(response))

    @step
    async def step_interrupt_one(self, ctx: Context, ev: JokeEvent) -> SecondEvent:
        print(f"> step_interrupt_one input : {ev.joke}")
        await asyncio.sleep(1)
        # wait until we see a HumanResponseEvent
        needs_answer = True
        response = await ctx.wait_for_event(
            InterruptResponseEvent,
            waiter_id="waiter_step_interrupt_one",
            waiter_event=FirstInterruptEvent(
                joke=ev.joke,
                first_question=f"What is your review about the Joke '{ev.joke}'?",
                needs_answer=needs_answer,
            ),
        )

        print(f"> receive response : {response.answer}")
        if needs_answer and not response.answer:
            raise ValueError("This needs a non-empty answer")

        return SecondEvent(
            joke=ev.joke, ai_answer=f"Received human answer: {response.answer}"
        )

    @step
    async def critique_joke(self, ev: SecondEvent) -> StopEvent:
        joke = ev.joke

        await asyncio.sleep(1)
        response = "this is a review for the joke: " + joke + "\n" + ev.ai_answer
        result = {
            joke: joke,
            "review": str(response),
        }
        return StopEvent(result=result)


def interrupt_workflow() -> JokeReviewer:
    joke_reviewer = JokeReviewer(timeout=None, verbose=True)
    return joke_reviewer


async def main():
    print("Joke Reviewer with Interrupts")
    workflow = interrupt_workflow()

    handler = workflow.run(topic="pirates")

    print("Reading events from the workflow...")
    async for ev in handler.stream_events():
        if isinstance(ev, FirstInterruptEvent):
            # capture keyboard input
            response = input(ev.first_question)
            print("Sending response event...")
            handler.ctx.send_event(
                InterruptResponseEvent(
                    answer=response,
                )
            )

    print("waiting for final result...")
    final_result = await handler
    print("Final result: ", final_result)


if __name__ == "__main__":
    asyncio.run(main())
