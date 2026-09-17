import logging

from typing import TypedDict, Annotated

from dotenv import load_dotenv

from langchain_core.messages import BaseMessage

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from langgraph.graph.message import add_messages

from langgraph.checkpoint.memory import MemorySaver

from src.agents_fixed import (
    retrieval_node,
    kpi_node,
    summary_node,
    risk_analysis_node,
    combine_financial_analysis_node,
    get_llm,
)


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# LOGGER
# --------------------------------------------------

logger = logging.getLogger(__name__)


# --------------------------------------------------
# SHARED STATE
# --------------------------------------------------

class AgentState(TypedDict, total=False):

    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    question: str

    agent: str

    answer: str

    sources: list

    requires_approval: bool

    approved: bool

    route: str

    metrics: dict

    error: str

    kpi_answer: str

    risk_answer: str


# --------------------------------------------------
# ROUTER AGENT
# --------------------------------------------------

def router_node(state: AgentState):

    logger.info(
        "Router Agent started"
    )

    question = state["messages"][-1].content

    llm = get_llm()

    prompt = f"""
You are a routing agent for a financial document assistant.

Classify the question into exactly one category.

Categories:

kpi:
Questions asking for a financial number or metric.

summary:
Questions asking for a summary or overview.

retrieval:
General questions about the financial documents.

financial_analysis:
Questions asking for financial performance analysis,
financial risks, growth analysis, or a detailed
assessment of the company's financial condition.

human_approval:
Questions asking whether to invest, buy, sell,
or make a financial recommendation.

Return only one word:

kpi
summary
retrieval
financial_analysis
human_approval

Question:
{question}
"""

    response = llm.invoke(prompt)

    decision = response.content

    if isinstance(decision, list):

        decision = "".join(

            item.get("text", "")
            if isinstance(item, dict)
            else str(item)

            for item in decision

        )

    decision = decision.strip().lower()


    # --------------------------------------------------
    # HUMAN APPROVAL RULE
    # --------------------------------------------------

    question_lower = question.lower()

    approval_keywords = [

        "invest",

        "buy",

        "sell",

        "recommendation",

        "should i",

    ]


    if any(

        keyword in question_lower

        for keyword in approval_keywords

    ):

        decision = "human_approval"


    # --------------------------------------------------
    # VALIDATE ROUTER OUTPUT
    # --------------------------------------------------

    valid_decisions = {

        "kpi",

        "summary",

        "retrieval",

        "financial_analysis",

        "human_approval",

    }


    if decision not in valid_decisions:

        logger.warning(

            "Invalid router decision: %s",

            decision,

        )

        decision = "retrieval"


    logger.info(

        "Router selected: %s",

        decision,

    )


    return {

        "question": question,

        "agent": decision,

        "route": decision,

        "requires_approval": (

            decision == "human_approval"

        ),

    }


# --------------------------------------------------
# ROUTING FUNCTION
# --------------------------------------------------

def route_decision(state: AgentState):

    agent = state.get(

        "agent",

        "retrieval",

    )


    if agent == "kpi":

        return "kpi_node"


    if agent == "summary":

        return "summary_node"


    if agent == "financial_analysis":

        return "financial_analysis"


    if agent == "human_approval":

        return "human_approval"


    return "retrieval_node"


# --------------------------------------------------
# HUMAN APPROVAL NODE
# --------------------------------------------------

def human_approval_node(state: AgentState):

    logger.info(

        "Human approval required"

    )

    return {

        "answer": (

            "This question requires human approval "
            "before a financial recommendation "
            "can be made."

        ),

        "agent": "human_approval",

        "requires_approval": True,

    }


# --------------------------------------------------
# FINANCIAL ANALYSIS ROUTE
# --------------------------------------------------

def financial_analysis_node(state: AgentState):

    logger.info(

        "Starting financial analysis"

    )

    return {

        "question": state["question"],

        "agent": "financial_analysis",

    }


# --------------------------------------------------
# CREATE WORKFLOW
# --------------------------------------------------

def create_workflow():

    workflow = StateGraph(AgentState)


    # --------------------------------------------------
    # ADD NODES
    # --------------------------------------------------

    workflow.add_node(

        "router",

        router_node,

    )


    workflow.add_node(

        "kpi_node",

        kpi_node,

    )


    workflow.add_node(

        "summary_node",

        summary_node,

    )


    workflow.add_node(

        "retrieval_node",

        retrieval_node,

    )


    workflow.add_node(

        "human_approval",

        human_approval_node,

    )


    workflow.add_node(

        "financial_analysis",

        financial_analysis_node,

    )


    workflow.add_node(

        "risk_analysis",

        risk_analysis_node,

    )


    workflow.add_node(

        "combine_financial_analysis",

        combine_financial_analysis_node,

    )


    # --------------------------------------------------
    # START → ROUTER
    # --------------------------------------------------

    workflow.add_edge(

        START,

        "router",

    )


    # --------------------------------------------------
    # ROUTER → AGENT
    # --------------------------------------------------

    workflow.add_conditional_edges(

        "router",

        route_decision,

        {

            "kpi_node": "kpi_node",

            "summary_node": "summary_node",

            "retrieval_node": "retrieval_node",

            "human_approval": "human_approval",

            "financial_analysis": "financial_analysis",

        },

    )


    # --------------------------------------------------
    # FINANCIAL ANALYSIS → KPI + RISK
    # --------------------------------------------------

    workflow.add_edge(

        "financial_analysis",

        "kpi_node",

    )


    workflow.add_edge(

        "financial_analysis",

        "risk_analysis",

    )


    # --------------------------------------------------
    # KPI + RISK → COMBINER
    # --------------------------------------------------

    workflow.add_edge(

        "kpi_node",

        "combine_financial_analysis",

    )


    workflow.add_edge(

        "risk_analysis",

        "combine_financial_analysis",

    )


    # --------------------------------------------------
    # OTHER AGENTS → END
    # --------------------------------------------------

    workflow.add_edge(

        "summary_node",

        END,

    )


    workflow.add_edge(

        "retrieval_node",

        END,

    )


    workflow.add_edge(

        "human_approval",

        END,

    )


    workflow.add_edge(

        "combine_financial_analysis",

        END,

    )


    # --------------------------------------------------
    # COMPILE
    # --------------------------------------------------

    return workflow.compile(

        checkpointer=MemorySaver()

    )