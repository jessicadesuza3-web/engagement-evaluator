Complete Streamlit App with Integrated Evaluator

Save this as app.py:

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from io import StringIO

# Page configuration
st.set_page_config(
    page_title="EMSA - Engagement Manager",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stakeholder-card {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #0066cc;
    }
    .score-excellent {
        color: #28a745;
        font-weight: bold;
    }
    .score-strong {
        color: #17a2b8;
        font-weight: bold;
    }
    .score-adequate {
        color: #ffc107;
        font-weight: bold;
    }
    .score-needs-improvement {
        color: #fd7e14;
        font-weight: bold;
    }
    .score-poor {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'engagements' not in st.session_state:
    st.session_state.engagements = {}

if 'current_engagement' not in st.session_state:
    st.session_state.current_engagement = None

if 'audit_history' not in st.session_state:
    st.session_state.audit_history = []

# Evaluation dimensions
DIMENSIONS = {
    'Stakeholder Identification & Mapping': {
        'weight': 0.12,
        'description': 'Does the agent comprehensively identify all relevant stakeholders and create structured, complete stakeholder maps?',
        'criteria': {
            5: 'Identifies all primary, secondary, and tertiary stakeholders with complete info. Proactively identifies hidden influencers.',
            4: 'Identifies all primary and secondary stakeholders with complete information. Minor gaps in tertiary stakeholders.',
            3: 'Identifies primary stakeholders with basic information. Some secondary stakeholders missed.',
            2: 'Misses key stakeholders. Incomplete information. Map lacks structure.',
            1: 'Fails to identify critical stakeholders. Map is unusable or missing.'
        }
    },
    'Influence & Interest Assessment': {
        'weight': 0.12,
        'description': 'Does the agent accurately assess influence and interest levels and position stakeholders correctly on a matrix?',
        'criteria': {
            5: 'All stakeholders correctly assessed. Matrix positioning accurate. Identifies power dynamics.',
            4: 'Most stakeholders correctly assessed. Minor misalignments. Matrix mostly accurate.',
            3: 'Stakeholders assessed but some ratings questionable. Matrix has gaps.',
            2: 'Multiple stakeholders misrated. Matrix incomplete or poorly justified.',
            1: 'Influence/interest assessment missing or fundamentally flawed.'
        }
    },
    'Sentiment Analysis & Tracking': {
        'weight': 0.15,
        'description': 'Does the agent accurately assess stakeholder sentiment and track changes over time?',
        'criteria': {
            5: 'All stakeholders have sentiment assessed. Updated after each interaction. Trends tracked.',
            4: 'Sentiment assessed for most stakeholders. Updated regularly. Minor gaps in documentation.',
            3: 'Sentiment assessed but not consistently updated. Some documentation of reasoning.',
            2: 'Sentiment assessment incomplete or outdated. Minimal tracking.',
            1: 'Sentiment assessment missing or inaccurate. No tracking.'
        }
    },
    'Engagement Strategy Development': {
        'weight': 0.20,
        'description': 'Does the agent develop tailored, strategic engagement approaches for each stakeholder?',
        'criteria': {
            5: 'Each stakeholder has customized strategy. Specific, actionable, outcome-focused. Includes messaging, frequency, channel.',
            4: 'Most stakeholders have tailored strategies. Clear and actionable. Minor gaps in specificity.',
            3: 'Engagement strategies exist but somewhat generic. Functional but lack customization.',
            2: 'Strategies are vague or one-size-fits-all. Limited customization.',
            1: 'No engagement strategies or strategies are ineffective.'
        }
    },
    'Communication Quality & Frequency': {
        'weight': 0.15,
        'description': 'Does the agent recommend and execute appropriate communication cadence and quality?',
        'criteria': {
            5: 'Communication frequency tailored to each stakeholder. Messages clear, concise, outcome-focused. Consistent execution.',
            4: 'Communication frequency appropriate. Messages generally clear and well-crafted. Good consistency.',
            3: 'Communication happens but frequency may be inconsistent. Messages adequate but could be more targeted.',
            2: 'Communication sporadic or poorly timed. Messages lack clarity or strategic focus.',
            1: 'Communication absent, ineffective, or counterproductive.'
        }
    },
    'Risk Identification & Mitigation': {
        'weight': 0.12,
        'description': 'Does the agent proactively identify engagement risks and develop mitigation strategies?',
        'criteria': {
            5: 'All major risks identified. Mitigation strategies specific and proactive. Risks monitored and updated.',
            4: 'Most risks identified. Mitigation strategies clear. Some monitoring of risk status.',
            3: 'Some risks identified. Mitigation strategies exist but may be generic. Limited monitoring.',
            2: 'Few risks identified. Mitigation strategies vague or missing.',
            1: 'Risks not identified or addressed.'
        }
    },
    'Outcome Tracking & Measurement': {
        'weight': 0.10,
        'description': 'Does the agent define success metrics and track progress toward engagement objectives?',
        'criteria': {
            5: 'Clear success metrics defined. Metrics are SMART. Progress tracked regularly. Outcomes documented.',
            4: 'Success metrics defined. Most are measurable. Progress tracked. Some outcomes documented.',
            3: 'Success metrics exist but may be vague. Limited tracking of progress.',
            2: 'Metrics unclear or missing. Minimal progress tracking.',
            1: 'No metrics or outcome tracking.'
        }
    },
    'Adaptability & Course Correction': {
        'weight': 0.04,
        'description': 'Does the agent adjust strategies based on feedback and changing circumstances?',
        'criteria': {
            5: 'Agent proactively adjusts strategies. Updates documented with rationale. Demonstrates learning.',
            4: 'Agent adjusts strategies when needed. Updates documented. Shows responsiveness.',
            3: 'Agent makes some adjustments but may be slow. Documentation inconsistent.',
            2: 'Agent slow to adapt. Limited evidence of strategy adjustments.',
            1: 'Agent does not adapt or adjust strategies. Rigid approach.'
        }
    }
}

def get_score_level(score):
    """Return performance level based on score"""
    if score >= 4.5:
        return 'Excellent'
    elif score >= 3.5:
        return 'Strong'
    elif score >= 2.5:
        return 'Adequate'
    elif score >= 1.5:
        return 'Needs Improvement'
    else:
        return 'Poor'

def calculate_overall_score(scores):
    """Calculate weighted overall score"""
    total = 0
    for dimension, score in scores.items():
        weight = DIMENSIONS[dimension]['weight']
        total += score * weight
    return round(total, 2)

def create_new_engagement(name, client, objectives, timeline_start, timeline_end):
    """Create a new engagement"""
    engagement_id = f"eng_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.engagements[engagement_id] = {
        'id': engagement_id,
        'name': name,
        'client': client,
        'objectives': objectives,
        'timeline_start': timeline_start,
        'timeline_end': timeline_end,
        'created_date': datetime.now().strftime('%Y-%m-%d'),
        'stakeholders': {},
        'timeline_milestones': [],
        'risks': [],
        'success_metrics': [],
        'updates': []
    }
    return engagement_id

def add_stakeholder(engagement_id, name, role, organization, influence, interest, sentiment, strategy):
    """Add stakeholder to engagement"""
    stakeholder_id = f"sh_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.engagements[engagement_id]['stakeholders'][stakeholder_id] = {
        'id': stakeholder_id,
        'name': name,
        'role': role,
        'organization': organization,
        'influence': influence,
        'interest': interest,
        'sentiment': sentiment,
        'strategy': strategy,
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'interaction_history': []
    }
    return stakeholder_id

# Main app
st.title("🤝 Engagement Manager Stakeholder Assistant (EMSA)")
st.subtitle("Comprehensive Engagement & Stakeholder Management Platform")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", [
    "🏠 Dashboard",
    "📋 Engagements",
    "👥 Stakeholder Map",
    "📅 Timeline & Milestones",
    "⚠️ Risk Management",
    "📊 Evaluator",
    "📈 Reports"
])

# DASHBOARD PAGE
if page == "🏠 Dashboard":
    st.header("Dashboard")
    
    if not st.session_state.engagements:
        st.info("No engagements yet. Go to 'Engagements' to create one.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Engagements", len(st.session_state.engagements))
        with col2:
            total_stakeholders = sum(len(e['stakeholders']) for e in st.session_state.engagements.values())
            st.metric("Total Stakeholders", total_stakeholders)
        with col3:
            total_risks = sum(len(e['risks']) for e in st.session_state.engagements.values())
            st.metric("Active Risks", total_risks)
        with col4:
            st.metric("Audit History", len(st.session_state.audit_history))
        
        st.markdown("---")
        st.subheader("Recent Engagements")
        
        for eng_id, engagement in list(st.session_state.engagements.items())[-5:]:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**{engagement['name']}**")
                st.caption(f"Client: {engagement['client']}")
            with col2:
                st.caption(f"Stakeholders: {len(engagement['stakeholders'])}")
                st.caption(f"Created: {engagement['created_date']}")
            with col3:
                if st.button("View", key=f"view_{eng_id}"):
                    st.session_state.current_engagement = eng_id
                    st.rerun()

# ENGAGEMENTS PAGE
elif page == "📋 Engagements":
    st.header("Engagements")
    
    tab1, tab2 = st.tabs(["Create New", "View All"])
    
    with tab1:
        st.subheader("Create New Engagement")
        
        col1, col2 = st.columns(2)
        with col1:
            engagement_name = st.text_input("Engagement Name", placeholder="e.g., Acme Corp Q1 2026")
            client_name = st.text_input("Client Name", placeholder="e.g., Acme Corporation")
        with col2:
            timeline_start = st.date_input("Start Date")
            timeline_end = st.date_input("End Date")
        
        objectives = st.text_area("Engagement Objectives", placeholder="List key objectives for this engagement", height=100)
        
        if st.button("Create Engagement", use_container_width=True):
            if engagement_name and client_name and objectives:
                eng_id = create_new_engagement(engagement_name, client_name, objectives, timeline_start, timeline_end)
                st.success(f"✅ Engagement '{engagement_name}' created!")
                st.session_state.current_engagement = eng_id
                st.rerun()
            else:
                st.error("Please fill in all required fields")
    
    with tab2:
        st.subheader("All Engagements")
        
        if not st.session_state.engagements:
            st.info("No engagements yet.")
        else:
            for eng_id, engagement in st.session_state.engagements.items():
                with st.expander(f"📌 {engagement['name']} ({engagement['client']})"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**Client:** {engagement['client']}")
                        st.markdown(f"**Created:** {engagement['created_date']}")
                    with col2:
                        st.markdown(f"**Timeline:** {engagement['timeline_start']} to {engagement['timeline_end']}")
                        st.markdown(f"**Stakeholders:** {len(engagement['stakeholders'])}")
                    with col3:
                        if st.button("Select", key=f"select_{eng_id}"):
                            st.session_state.current_engagement = eng_id
                            st.rerun()
                        if st.button("Delete", key=f"delete_{eng_id}"):
                            del st.session_state.engagements[eng_id]
                            st.rerun()
                    
                    st.markdown("**Objectives:**")
                    st.write(engagement['objectives'])

# STAKEHOLDER MAP PAGE
elif page == "👥 Stakeholder Map":
    st.header("Stakeholder Map")
    
    if not st.session_state.engagements:
        st.info("No engagements yet. Create one first.")
    else:
        # Select engagement
        eng_options = {eng_id: eng['name'] for eng_id, eng in st.session_state.engagements.items()}
        selected_eng = st.selectbox("Select Engagement", list(eng_options.keys()), format_func=lambda x: eng_options[x])
        engagement = st.session_state.engagements[selected_eng]
        
        tab1, tab2 = st.tabs(["Add Stakeholder", "View Map"])
        
        with tab1:
            st.subheader("Add New Stakeholder")
            
            col1, col2 = st.columns(2)
            with col1:
                sh_name = st.text_input("Stakeholder Name")
                sh_role = st.text_input("Role/Title")
                sh_org = st.text_input("Organization")
            with col2:
                sh_influence = st.selectbox("Influence Level", ["High", "Medium", "Low"])
                sh_interest = st.selectbox("Interest Level", ["High", "Medium", "Low"])
                sh_sentiment = st.selectbox("Sentiment", ["Champion", "Neutral", "Skeptic"])
            
            sh_strategy = st.text_area("Engagement Strategy", placeholder="Describe how to engage this stakeholder", height=100)
            
            if st.button("Add Stakeholder", use_container_width=True):
                if sh_name and sh_role and sh_org and sh_strategy:
                    add_stakeholder(selected_eng, sh_name, sh_role, sh_org, sh_influence, sh_interest, sh_sentiment, sh_strategy)
                    st.success(f"✅ Stakeholder '{sh_name}' added!")
                    st.rerun()
                else:
                    st.error("Please fill in all fields")
        
        with tab2:
            st.subheader("Stakeholder Map")
            
            if not engagement['stakeholders']:
                st.info("No stakeholders added yet.")
            else:
                # Influence/Interest Matrix
                st.markdown("### Influence/Interest Matrix")
                
                matrix_data = {
                    'High Influence\nHigh Interest': [],
                    'High Influence\nLow Interest': [],
                    'Low Influence\nHigh Interest': [],
                    'Low Influence\nLow Interest': []
                }
                
                for sh_id, stakeholder in engagement['stakeholders'].items():
                    influence = stakeholder['influence']
                    interest = stakeholder['interest']
                    
                    if influence == 'High' and interest == 'High':
                        key = 'High Influence\nHigh Interest'
                    elif influence == 'High' and interest != 'High':
                        key = 'High Influence\nLow Interest'
                    elif influence != 'High' and interest == 'High':
                        key = 'Low Influence\nHigh Interest'
                    else:
                        key = 'Low Influence\nLow Interest'
                    
                    matrix_data[key].append(stakeholder['name'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Manage Closely** (High Influence, High Interest)")
                    for name in matrix_data['High Influence\nHigh Interest']:
                        st.success(f"✅ {name}")
                    
                    st.markdown("**Keep Satisfied** (Low Influence, High Interest)")
                    for name in matrix_data['Low Influence\nHigh Interest']:
                        st.info(f"ℹ️ {name}")
                
                with col2:
                    st.markdown("**Keep Informed** (High Influence, Low Interest)")
                    for name in matrix_data['High Influence\nLow Interest']:
                        st.warning(f"⚠️ {name}")
                    
                    st.markdown("**Monitor** (Low Influence, Low Interest)")
                    for name in matrix_data['Low Influence\nLow Interest']:
                        st.caption(f"• {name}")
                
                st.markdown("---")
                st.markdown("### Detailed Stakeholder List")
                
                for sh_id, stakeholder in engagement['stakeholders'].items():
                    with st.expander(f"👤 {stakeholder['name']} - {stakeholder['role']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Organization:** {stakeholder['organization']}")
                            st.markdown(f"**Influence:** {stakeholder['influence']}")
                            st.markdown(f"**Interest:** {stakeholder['interest']}")
                        with col2:
                            st.markdown(f"**Sentiment:** {stakeholder['sentiment']}")
                            st.markdown(f"**Last Updated:** {stakeholder['last_updated']}")
                        
                        st.markdown("**Engagement Strategy:**")
                        st.write(stakeholder['strategy'])
                        
                        # Update sentiment
                        new_sentiment = st.selectbox("Update Sentiment", ["Champion", "Neutral", "Skeptic"], key=f"sentiment_{sh_id}")
                        if st.button("Update", key=f"update_sentiment_{sh_id}"):
                            engagement['stakeholders'][sh_id]['sentiment'] = new_sentiment
                            engagement['stakeholders'][sh_id]['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                            st.success("✅ Sentiment updated!")
                            st.rerun()

# TIMELINE & MILESTONES PAGE
elif page == "📅 Timeline & Milestones":
    st.header("Timeline & Milestones")
    
    if not st.session_state.engagements:
        st.info("No engagements yet.")
    else:
        eng_options = {eng_id: eng['name'] for eng_id, eng in st.session_state.engagements.items()}
        selected_eng = st.selectbox("Select Engagement", list(eng_options.keys()), format_func=lambda x: eng_options[x])
        engagement = st.session_state.engagements[selected_eng]
        
        tab1, tab2 = st.tabs(["Add Milestone", "View Timeline"])
        
        with tab1:
            st.subheader("Add Milestone")
            
            col1, col2 = st.columns(2)
            with col1:
                milestone_name = st.text_input("Milestone Name")
                milestone_date = st.date_input("Target Date")
            with col2:
                milestone_owner = st.text_input("Owner")
                milestone_status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
            
            milestone_description = st.text_area("Description", height=100)
            
            if st.button("Add Milestone", use_container_width=True):
                if milestone_name and milestone_owner and milestone_description:
                    engagement['timeline_milestones'].append({
                        'name': milestone_name,
                        'date': milestone_date.strftime('%Y-%m-%d'),
                        'owner': milestone_owner,
                        'status': milestone_status,
                        'description': milestone_description
                    })
                    st.success("✅ Milestone added!")
                    st.rerun()
                else:
                    st.error("Please fill in all fields")
        
        with tab2:
            st.subheader("Engagement Timeline")
            
            if not engagement['timeline_milestones']:
                st.info("No milestones added yet.")
            else:
                # Sort by date
                sorted_milestones = sorted(engagement['timeline_milestones'], key=lambda x: x['date'])
                
                for idx, milestone in enumerate(sorted_milestones):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**{milestone['name']}**")
                        st.caption(milestone['description'])
                    with col2:
                        st.caption(f"📅 {milestone['date']}")
                        st.caption(f"Owner: {milestone['owner']}")
                    with col3:
                        status_color = "🟢" if milestone['status'] == "Completed" else "🟡" if milestone['status'] == "In Progress" else "⚪"
                        st.caption(f"{status_color} {milestone['status']}")

# RISK MANAGEMENT PAGE
elif page == "⚠️ Risk Management":
    st.header("Risk Management")
    
    if not st.session_state.engagements:
        st.info("No engagements yet.")
    else:
        eng_options = {eng_id: eng['name'] for eng_id, eng in st.session_state.engagements.items()}
        selected_eng = st.selectbox("Select Engagement", list(eng_options.keys()), format_func=lambda x: eng_options[x])
        engagement = st.session_state.engagements[selected_eng]
        
        tab1, tab2 = st.tabs(["Add Risk", "View Risks"])
        
        with tab1:
            st.subheader("Add Risk")
            
            col1, col2 = st.columns(2)
            with col1:
                risk_name = st.text_input("Risk Name")
                risk_probability = st.selectbox("Probability", ["High", "Medium", "Low"])
            with col2:
                risk_impact = st.selectbox("Impact", ["High", "Medium", "Low"])
                risk_status = st.selectbox("Status", ["Active", "Mitigated", "Resolved"])
            
            risk_description = st.text_area("Risk Description", height=80)
            risk_mitigation = st.text_area("Mitigation Strategy", height=80)
            
            if st.button("Add Risk", use_container_width=True):
                if risk_name and risk_description and risk_mitigation:
                    engagement['risks'].append({
                        'name': risk_name,
                        'probability': risk_probability,
                        'impact': risk_impact,
                        'status': risk_status,
                        'description': risk_description,
                        'mitigation': risk_mitigation,
                        'created_date': datetime.now().strftime('%Y-%m-%d')
                    })
                    st.success("✅ Risk added!")
                    st.rerun()
                else:
                    st.error("Please fill in all fields")
        
        with tab2:
            st.subheader("Risk Register")
            
            if not engagement['risks']:
                st.info("No risks identified yet.")
            else:
                for idx, risk in enumerate(engagement['risks']):
                    severity = "🔴" if (risk['probability'] == "High" and risk['impact'] == "High") else "🟠" if (risk['probability'] in ["High", "Medium"] or risk['impact'] in ["High", "Medium"]) else "🟡"
                    
                    with st.expander(f"{severity} {risk['name']} ({risk['status']})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Probability:** {risk['probability']}")
                            st.markdown(f"**Impact:** {risk['impact']}")
                        with col2:
                            st.markdown(f"**Status:** {risk['status']}")
                            st.markdown(f"**Created:** {risk['created_date']}")
                        
                        st.markdown("**Description:**")
                        st.write(risk['description'])
                        
                        st.markdown("**Mitigation Strategy:**")
                        st.write(risk['mitigation'])

# EVALUATOR PAGE
elif page == "📊 Evaluator":
    st.header("Agent Performance Evaluator")
    
    st.markdown("""
    This evaluator assesses the performance of the Engagement Manager Stakeholder Assistant 
    across 8 key dimensions based on best practices in stakeholder management.
    """)
    
    tab1, tab2, tab3 = st.tabs(["Conduct Audit", "View Results", "Framework"])
    
    with tab1:
        st.subheader("Conduct an Audit")
        
        if not st.session_state.engagements:
            st.info("No engagements to audit yet.")
        else:
            eng_options = {eng_id: eng['name'] for eng_id, eng in st.session_state.engagements.items()}
            selected_eng = st.selectbox("Select Engagement to Audit", list(eng_options.keys()), format_func=lambda x: eng_options[x])
            engagement = st.session_state.engagements[selected_eng]
            
            audit_date = st.date_input("Audit Date")
            
            st.markdown("---")
            st.subheader("Score Each Dimension (1-5)")
            
            scores = {}
            for dimension, details in DIMENSIONS.items():
                st.markdown(f"### {dimension}")
                st.caption(details['description'])
                
                with st.expander("View Scoring Criteria"):
                    for score in [5, 4, 3, 2, 1]:
                        st.markdown(f"**{score}:** {details['criteria'][score]}")
                
                score = st.slider(
                    f"Score for {dimension}",
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"score_{dimension}"
                )
                scores[dimension] = score
                st.markdown("---")
            
            overall_score = calculate_overall_score(scores)
            
            st.markdown("### Audit Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Score", f"{overall_score}/5.0")
            with col2:
                st.metric("Performance Level", get_score_level(overall_score))
            with col3:
                st.metric("Engagement", engagement['name'])
            
            st.markdown("### Audit Findings")
            
            col1, col2 = st.columns(2)
            with col1:
                strengths = st.text_area(
                    "Key Strengths (one per line)",
                    height=150,
                    placeholder="e.g., Excellent stakeholder mapping\nStrong sentiment tracking"
                )
            with col2:
                gaps = st.text_area(
                    "Gaps & Improvement Areas (one per line)",
                    height=150,
                    placeholder="e.g., Risk mitigation strategies need more specificity"
                )
            
            recommendations = st.text_area(
                "Recommended Actions (one per line)",
                height=150,
                placeholder="e.g., Implement weekly risk monitoring"
            )
            
            if st.button("💾 Save Audit", use_container_width=True):
                audit_record = {
                    'date': audit_date.strftime('%Y-%m-%d'),
                    'engagement_name': engagement['name'],
                    'engagement_id': selected_eng,
                    'scores': scores,
                    'overall_score': overall_score,
                    'strengths': [s.strip() for s in strengths.split('\n') if s.strip()],
                    'gaps': [g.strip() for g in gaps.split('\n') if g.strip()],
                    'recommendations': [r.strip() for r in recommendations.split('\n') if r.strip()]
                }
                st.session_state.audit_history.append(audit_record)
                st.success("✅ Audit saved successfully!")
                st.balloons()
    
    with tab2:
        st.subheader("Audit Results")
        
        if not st.session_state.audit_history:
            st.info("No audits conducted yet.")
        else:
            audit_options = [f"{a['date']} - {a['engagement_name']}" for a in st.session_state.audit_history]
            selected_audit_idx = st.selectbox("Select Audit", range(len(audit_options)), format_func=lambda x: audit_options[x])
            
            audit = st.session_state.audit_history[selected_audit_idx]
            
            st.markdown(f"### {audit['engagement_name']}")
            st.caption(f"Audit Date: {audit['date']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Score", f"{audit['overall_score']}/5.0")
            with col2:
                st.metric("Performance Level", get_score_level(audit['overall_score']))
            with col3:
                if audit['overall_score'] >= 4.5:
                    rec = "Continue current approach"
                elif audit['overall_score'] >= 3.5:
                    rec = "Maintain work, address gaps"
                elif audit['overall_score'] >= 2.5:
                    rec = "Provide coaching"
                elif audit['overall_score'] >= 1.5:
                    rec = "Significant coaching needed"
                else:
                    rec = "Immediate intervention"
                st.metric("Recommendation", rec)
            
            st.markdown("### Dimension Scores")
            
            dimension_data = []
            for dimension, score in audit['scores'].items():
                weight = DIMENSIONS[dimension]['weight']
                dimension_data.append({
                    'Dimension': dimension,
                    'Score': score,
                    'Weight': f"{weight*100:.0f}%"
                })
            
            df_dimensions = pd.DataFrame(dimension_data)
            st.dataframe(df_dimensions, use_container_width=True, hide_index=True)
            
            st.markdown("### Score Distribution")
            fig_data = {
                'Dimension': list(audit['scores'].keys()),
                'Score': list(audit['scores'].values())
            }
            df_chart = pd.DataFrame(fig_data)
            st.bar_chart(df_chart.set_index('Dimension')['Score'], height=400)
            
            st.markdown("### Key Strengths")
            for strength in audit['strengths']:
                st.success(f"✅ {strength}")
            
            st.markdown("### Gaps & Improvement Areas")
            for gap in audit['gaps']:
                st.warning(f"⚠️ {gap}")
            
            st.markdown("### Recommended Actions")
            for idx, rec in enumerate(audit['recommendations'], 1):
                st.info(f"{idx}. {rec}")
    
    with tab3:
        st.subheader("Evaluation Framework Reference")
        
        st.markdown("### Scoring Scale")
        scoring_data = {
            'Score': [5, 4, 3, 2, 1],
            'Level': ['Excellent', 'Strong', 'Adequate', 'Needs Improvement', 'Poor'],
            'Description': [
                'Exceeds expectations, strategic, proactive, measurable outcomes',
                'Meets expectations, well-executed, good outcomes',
                'Meets basic requirements, functional, acceptable outcomes',
                'Below expectations, gaps in execution',
                'Significant gaps, ineffective'
            ]
        }
        df_scoring = pd.DataFrame(scoring_data)
        st.dataframe(df_scoring, use_container_width=True, hide_index=True)
        
        st.markdown("### The 8 Evaluation Dimensions")
        
        for dimension, details in DIMENSIONS.items():
            with st.expander(f"{dimension} (Weight: {details['weight']*100:.0f}%)"):
                st.markdown(f"**Description:** {details['description']}")
                st.markdown("**Scoring Criteria:**")
                for score in [5, 4, 3, 2, 1]:
                    st.markdown(f"- **{score}:** {details['criteria'][score]}")

# REPORTS PAGE
elif page == "📈 Reports":
    st.header("Reports & Analytics")
    
    if not st.session_state.engagements:
        st.info("No engagements yet.")
    else:
        tab1, tab2, tab3 = st.tabs(["Engagement Summary", "Stakeholder Analysis", "Audit Trends"])
        
        with tab1:
            st.subheader("Engagement Summary")
            
            eng_options = {eng_id: eng['name'] for eng_id, eng in st.session_state.engagements.items()}
            selected_eng = st.selectbox("Select Engagement", list(eng_options.keys()), format_func=lambda x: eng_options[x], key="report_eng")
            engagement = st.session_state.engagements[selected_eng]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Stakeholders", len(engagement['stakeholders']))
            with col2:
                st.metric("Milestones", len(engagement['timeline_milestones']))
            with col3:
                st.metric("Active Risks", len([r for r in engagement['risks'] if r['status'] == 'Active']))
            with col4:
                st.metric("Success Metrics", len(engagement['success_metrics']))
            
            st.markdown("### Engagement Details")
            st.markdown(f"**Client:** {engagement['client']}")
            st.markdown(f"**Timeline:** {engagement['timeline_start']} to {engagement['timeline_end']}")
            st.markdown(f"**Created:** {engagement['created_date']}")
            st.markdown(f"**Objectives:** {engagement['objectives']}")
        
        with tab2:
            st.subheader("Stakeholder Analysis")
            
            eng_options = {eng_id: eng['name'] for eng_id, eng in st.session_state.engagements.items()}
            selected_eng = st.selectbox("Select Engagement", list(eng_options.keys()), format_func=lambda x: eng_options[x], key="stakeholder_eng")
            engagement = st.session_state.engagements[selected_eng]
            
            if engagement['stakeholders']:
                # Sentiment breakdown
                sentiment_counts = {'Champion': 0, 'Neutral': 0, 'Skeptic': 0}
                for sh in engagement['stakeholders'].values():
                    sentiment_counts[sh['sentiment']] += 1
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Champions", sentiment_counts['Champion'])
                with col2:
                    st.metric("Neutral", sentiment_counts['Neutral'])
                with col3:
                    st.metric("Skeptics", sentiment_counts['Skeptic'])
                
                # Influence breakdown
                st.markdown("### Influence Distribution")
                influence_counts = {'High': 0, 'Medium': 0, 'Low': 0}
                for sh in engagement['stakeholders'].values():
                    influence_counts[sh['influence']] += 1
                
                df_influence = pd.DataFrame({
                    'Influence Level': list(influence_counts.keys()),
                    'Count': list(influence_counts.values())
                })
                st.bar_chart(df_influence.set_index('Influence Level')['Count'])
            else:
                st.info("No stakeholders in this engagement.")
        
        with tab3:
            st.subheader("Audit Trends")
            
            if not st.session_state.audit_history:
                st.info("No audits conducted yet.")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Audits", len(st.session_state.audit_history))
                with col2:
                    avg_score = np.mean([a['overall_score'] for a in st.session_state.audit_history])
                    st.metric("Average Score", f"{avg_score:.2f}/5.0")
                with col3:
                    latest_score = st.session_state.audit_history[-1]['overall_score']
                    st.metric("Latest Score", f"{latest_score}/5.0")
                
                st.markdown("### Score Trend")
                trend_data = {
                    'Date': [a['date'] for a in st.session_state.audit_history],
                    'Score': [a['overall_score'] for a in st.session_state.audit_history]
                }
                df_trend = pd.DataFrame(trend_data)
                st.line_chart(df_trend.set_index('Date')['Score'], height=400)
                
                st.markdown("### All Audits")
                table_data = []
                for audit in st.session_state.audit_history:
                    table_data.append({
                        'Date': audit['date'],
                        'Engagement': audit['engagement_name'],
                        'Score': f"{audit['overall_score']}/5.0",
                        'Level': get_score_level(audit['overall_score'])
                    })
                
                df_table = pd.DataFrame(table_data)
                st.dataframe(df_table, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Engagement Manager Stakeholder Assistant (EMSA)</p>
    <p style='font-size: 0.8em; color: gray;'>Built with Streamlit | Integrated Evaluator | Stakeholder Management Platform</p>
</div>
""", unsafe_allow_html=True)

