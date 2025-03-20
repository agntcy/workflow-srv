import pytest
from pytest_mock import MockerFixture

from agent_workflow_server.agents.load import (
    AGENTS,
    get_agent,
    get_agent_info,
    load_agents,
    search_agents,
)
from agent_workflow_server.generated.models.agent_search_request import (
    AgentSearchRequest,
)
from tests.mock import MOCK_AGENTS_REF_ENV, MOCK_MANIFEST_ENV, MockAdapter, MockAgent


def test_load_agents(mocker: MockerFixture):
    mocker.patch.dict("os.environ", MOCK_AGENTS_REF_ENV)
    mocker.patch.dict("os.environ", MOCK_MANIFEST_ENV)
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    load_agents()

    assert len(AGENTS) == 1
    assert isinstance(AGENTS["mock_agent"].agent, MockAgent)


@pytest.mark.parametrize(
    "agent_id, expected", [("mock_agent", True), ("another_id", False)]
)
def test_get_agent_info(mocker: MockerFixture, agent_id: str, expected: bool):
    mocker.patch.dict("os.environ", MOCK_AGENTS_REF_ENV)
    mocker.patch.dict("os.environ", MOCK_MANIFEST_ENV)
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    load_agents()

    assert len(AGENTS) == 1

    try:
        _ = get_agent_info(agent_id)
        assert expected
    except Exception:
        assert not expected


@pytest.mark.parametrize(
    "agent_id, expected", [("mock_agent", True), ("another_id", False)]
)
def test_get_agent(mocker: MockerFixture, agent_id: str, expected: bool):
    mocker.patch.dict("os.environ", MOCK_AGENTS_REF_ENV)
    mocker.patch.dict("os.environ", MOCK_MANIFEST_ENV)
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    load_agents()

    assert len(AGENTS) == 1

    try:
        agent = get_agent(agent_id)
        assert expected
        assert agent.agent_id == agent_id
        assert agent.metadata == AGENTS[agent_id].manifest.metadata
    except Exception:
        assert not expected


@pytest.mark.parametrize(
    "name, version, expected, exception",
    [
        ("org.agntcy.mock_agent", None, 1, False),
        ("org.agntcy.mock_agent", "0.0.1", 1, False),
        (None, "0.0.1", 1, False),
        ("another_id", None, 0, False),
        ("mock_agent", None, 0, False),
        ("another_id", "0.0.1", 0, False),
        (None, None, 0, True),
        ("org.agntcy.mock_agent", "0.0.2", 0, False),
        (None, "0.0.2", 0, False),
    ],
)
def test_search_agents(
    mocker: MockerFixture, name: str, version: str, expected: int, exception: bool
):
    mocker.patch.dict("os.environ", MOCK_AGENTS_REF_ENV)
    mocker.patch.dict("os.environ", MOCK_MANIFEST_ENV)
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    load_agents()

    assert len(AGENTS) == 1

    try:
        agents = search_agents(AgentSearchRequest(name=name, version=version))
        assert not exception
        assert len(agents) == expected
    except Exception:
        assert exception
