# Email Reviewer (Agentless)

A simple agent written using Agentless platform provided by the server.

## Agent Input
- `email`: (str) Email to review
- `audience`: (str) one of `general`, `technical`, `business`, `academic`

## Agent Output
- `correct`: (bool) If given email does not contain writing errors and it targets the audience correctly.
- `corrected_email`: (opt, str) The corrected email

## Agent local deployment

Set up the environment for the workflow server. You can create the `.env` file
where the workflow server is executed. It will also need credentials for 
whichever LLM you use in the Agentless platform.

```
AGENT_MANIFEST_PATH=examples/email_reviewer_agentless/deploy/email_reviewer_agentless.json
AGENTS_REF='{"3f1e2549-5799-4321-91ae-2a4881d55526": "agent_workflow_server.agents.adapters.agentless:dummyagent"}'
AZURE_OPENAI_API_KEY=blah-blah-blah
AZURE_OPENAI_ENDPOINT=blah-blah-blah
OPENAI_API_VERSION=2024-07-01-preview
```

Deploy the workflow (from the top-level of the repo): `python run server`

## Test agent

Point your browser at the [workflow server after running the agent](http://127.0.0.1:8000/agents/3f1e2549-5799-4321-91ae-2a4881d55526/docs#/Stateless%20Runs/create_and_wait_for_stateless_run_output)
