"""
Streamlit UI components for Investment Recommendation & Human Approval
"""

import streamlit as st
from datetime import datetime
from src.approval_manager import create_approval_request, get_pending_approvals
from src.investment_recommendation_agent import (
    format_recommendation_for_approval,
    create_user_response,
)


def display_investment_recommendation(state: dict):
    """
    Display investment recommendation awaiting approval.
    Shows to the user what they asked, what the AI recommends,
    and that it's waiting for human review.
    """

    st.info("""
    🔍 **Investment Question Detected**

    Your investment-related question requires human analyst review.
    The AI has prepared an analysis that will be reviewed before
    being shared with you.
    """)

    with st.expander("📊 AI-Generated Analysis (Pending Review)", expanded=True):
        # Show the recommendation being reviewed
        recommendation = state.get("answer", "Preparing analysis...")
        st.markdown(recommendation)

        # Show supporting analysis
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💰 Financial Analysis")
            kpi_analysis = state.get("kpi_analysis", "")
            if kpi_analysis:
                st.text(kpi_analysis[:300] + "...")

        with col2:
            st.subheader("⚠️ Risk Assessment")
            risk_analysis = state.get("risk_analysis", "")
            if risk_analysis:
                st.text(risk_analysis[:300] + "...")

    # Show approval status
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", "⏳ Pending Review")
    with col2:
        approval_id = state.get("approval_id", "N/A")
        st.metric("Request ID", approval_id[:8] if approval_id else "N/A")
    with col3:
        st.metric("Timeline", "< 24 hours")

    # Instructions
    st.divider()

    st.markdown("""
    ### What Happens Next?

    1. 📤 Your question has been submitted for review
    2. 👨‍💼 A financial analyst will review the AI's analysis
    3. ✅ They will approve, request changes, or reject
    4. 📧 You'll be notified when review is complete

    ### Important Disclaimer

    This analysis is for informational purposes only and should not be
    considered financial advice. Please consult with a qualified
    financial advisor before making investment decisions.
    """)


def show_approval_manager_interface():
    """
    Analyst/Manager interface for reviewing and approving
    investment recommendations.

    This would typically be in a separate dashboard tab.
    """

    st.title("📊 Investment Recommendation Review")

    st.markdown("""
    This interface allows financial analysts to review, approve, or
    request changes to AI-generated investment recommendations.
    """)

    # Get pending approvals
    pending = get_pending_approvals()

    if not pending:
        st.success("✅ No pending approvals")
        return

    st.subheader(f"Pending Reviews ({len(pending)})")

    for request in pending:
        with st.expander(
            f"📋 {request.question[:60]}... | ID: {request.id}",
            expanded=False
        ):
            # Question and analysis
            st.markdown("#### Question Asked")
            st.write(request.question)

            st.divider()

            st.markdown("#### AI Analysis")
            st.write(request.response)

            st.divider()

            # Risk assessment
            st.markdown("#### Risk Factors Identified")
            for factor in request.risk_factors:
                st.caption(f"⚠️ {factor}")

            st.markdown("#### Confidence Score")
            st.progress(request.confidence)
            st.caption(f"{request.confidence * 100:.0f}%")

            st.divider()

            # Approval decision
            st.markdown("#### Your Decision")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ Approve", key=f"approve_{request.id}"):
                    analyst_notes = st.text_input(
                        "Optional notes:",
                        key=f"notes_{request.id}"
                    )

                    # In real system, would update approval_manager
                    st.success(f"✅ Request {request.id} approved!")
                    st.balloons()

                    # Show what user will receive
                    st.info("User will receive:")
                    user_response = create_user_response(
                        recommendation=request.response,
                        approval_status="approved",
                        analyst_notes=analyst_notes
                    )
                    st.markdown(user_response)

            with col2:
                if st.button("🔄 Request Changes", key=f"changes_{request.id}"):
                    feedback = st.text_area(
                        "What changes are needed?",
                        key=f"feedback_{request.id}",
                        height=100
                    )

                    if feedback:
                        st.warning(f"""
                        Request {request.id} marked for revision.

                        Feedback sent to AI:
                        "{feedback}"

                        AI will regenerate the recommendation.
                        """)

            with col3:
                if st.button("❌ Reject", key=f"reject_{request.id}"):
                    reason = st.text_area(
                        "Reason for rejection:",
                        key=f"reason_{request.id}",
                        height=100
                    )

                    st.error(f"""
                    Request {request.id} rejected.

                    User will be notified that the recommendation
                    was not approved for release.
                    """)


def show_investment_recommendation_flow():
    """
    Show a visual diagram of how investment recommendations flow through
    approval process.
    """

    st.markdown("""
    ## Investment Recommendation Workflow

    ```
    User Question
        ↓
    "Can I invest in ABC Company?"
        ↓
    Investment Intent Detection
        ↓
    AI Analysis (KPIs + Risks)
        ↓
    AI Generates Recommendation
        ↓
    ┌─ HUMAN APPROVAL REQUIRED ─┐
    │                           │
    ├→ Approved → Release to User
    │
    ├→ Changes Requested → Regenerate
    │
    └→ Rejected → Inform User
    ```

    ### What Gets Reviewed

    | Item | Reviewer Checks |
    |------|-----------------|
    | **Financial Analysis** | Are the KPIs correct? |
    | **Risk Assessment** | Are all risks identified? |
    | **Recommendation Logic** | Is the analysis sound? |
    | **Confidence Level** | Is the AI confident enough? |
    | **Compliance** | Does it meet regulatory requirements? |

    ### Possible Outcomes

    | Decision | Result | User Sees |
    |----------|--------|-----------|
    | ✅ **Approve** | Recommendation released | Full analysis + "Human Reviewed" |
    | 🔄 **Changes** | AI regenerates | Revised analysis after changes |
    | ❌ **Reject** | Not released | "Recommendation not approved" |
    """)


def simulate_approval_process():
    """
    Simulation mode - shows how the approval process works
    without requiring real human interaction.

    Good for demos and testing.
    """

    st.subheader("📋 Approval Process Simulation")

    st.info("""
    This demonstrates how the investment recommendation
    approval process works end-to-end.
    """)

    # Step 1: Question
    st.markdown("### Step 1: User Asks Investment Question")
    question = "Should I invest in TechCorp Industries?"
    st.code(f'User: "{question}"')

    # Step 2: AI Analysis
    st.markdown("### Step 2: AI Generates Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**KPI Analysis**")
        st.caption("""
        Revenue Growth: 15% YoY
        Profit Margin: 18%
        Debt-to-Equity: 0.65
        """)
    with col2:
        st.markdown("**Risk Assessment**")
        st.caption("""
        ⚠️ Market Competition
        ⚠️ Technology Risks
        ⚠️ R&D Dependency
        """)

    # Step 3: Recommendation
    st.markdown("### Step 3: AI Creates Recommendation")
    st.text_area(
        "AI Recommendation Draft:",
        value="""Based on the financial analysis, TechCorp shows positive
growth metrics and manageable debt levels. However, the company
faces significant competitive pressures in the technology sector.

The investment may be suitable for growth-oriented investors with
moderate risk tolerance. Further due diligence is recommended.""",
        height=120,
        disabled=True
    )

    # Step 4: Human Review
    st.markdown("### Step 4: Human Analyst Review")
    st.info("""
    Manager: Jane Smith
    Time: 2026-09-17 14:30:00
    Review Time: 12 minutes
    """)

    decision = st.radio(
        "Analyst Decision:",
        ["✅ Approve", "🔄 Request Changes", "❌ Reject"],
        horizontal=True
    )

    if decision == "✅ Approve":
        notes = st.text_area(
            "Approval Notes (optional):",
            "Reviewed with compliance. Suitable for growth portfolio."
        )

        st.success("✅ Recommendation Approved!")

        st.markdown("### Step 5: User Receives Response")

        response = f"""
        INVESTMENT RESEARCH ANALYSIS
        ═══════════════════════════════════════════════════════════

        Based on the financial documents provided, TechCorp Industries
        shows positive growth metrics and manageable debt levels.
        However, the company faces significant competitive pressures
        in the technology sector.

        The investment may be suitable for growth-oriented investors
        with moderate risk tolerance.

        ───────────────────────────────────────────────────────────

        ✅ APPROVAL STATUS: Human Reviewed
        Review Date: 2026-09-17 14:30
        Analyst Notes: {notes}

        ───────────────────────────────────────────────────────────

        IMPORTANT DISCLAIMER:

        This analysis is for informational purposes only. Please
        consult with a qualified financial advisor before making
        investment decisions.
        """

        st.text_area(
            "What User Receives:",
            value=response,
            height=300,
            disabled=True
        )

    elif decision == "🔄 Request Changes":
        feedback = st.text_area(
            "Requested Changes:",
            "Please verify the debt-to-equity ratio against the latest Q3 filing."
        )

        st.warning(f"""
        🔄 Changes Requested:
        "{feedback}"

        AI will regenerate the recommendation with corrections.
        """)

    else:  # Reject
        reason = st.text_area(
            "Rejection Reason:",
            "Insufficient data from latest quarterly reports."
        )

        st.error(f"""
        ❌ Recommendation Rejected

        Reason: {reason}

        User will be notified that this recommendation
        could not be approved at this time.
        """)
