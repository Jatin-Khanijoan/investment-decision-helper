#!/usr/bin/env python3
"""
Kautilya Streamlit GUI Frontend
A modern web interface for NIFTY50 investment decision system
"""

import streamlit as st
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import backend modules
from providers.utils import load_universe, validate_symbol
# from graph import build_graph
from graph_rl import build_rl_graph as build_graph

from state import DecisionState

# Configure page
st.set_page_config(
    page_title="Kautilya - NIFTY50 Investment Advisor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .decision-card {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid;
    }
    .buy-card { border-left-color: #28a745; background-color: #d4edda; }
    .sell-card { border-left-color: #dc3545; background-color: #f8d7da; }
    .hold-card { border-left-color: #ffc107; background-color: #fff3cd; }
    .confidence-high { color: #28a745; font-weight: bold; }
    .confidence-medium { color: #ffc107; font-weight: bold; }
    .confidence-low { color: #dc3545; font-weight: bold; }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'decision_result' not in st.session_state:
    st.session_state.decision_result = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'logs' not in st.session_state:
    st.session_state.logs = ""

def load_nifty50_symbols() -> list:
    """Load NIFTY50 symbols from stocks.json"""
    try:
        universe = load_universe("stocks.json")
        return sorted(universe)
    except Exception as e:
        st.error(f"Error loading NIFTY50 symbols: {e}")
        return []

def get_confidence_color(confidence: float) -> str:
    """Return CSS class based on confidence level"""
    if confidence >= 0.7:
        return "confidence-high"
    elif confidence >= 0.4:
        return "confidence-medium"
    else:
        return "confidence-low"

def get_decision_card_class(decision: str) -> str:
    """Return CSS class based on decision type"""
    decision_upper = decision.upper()
    if decision_upper == "BUY":
        return "buy-card"
    elif decision_upper == "SELL":
        return "sell-card"
    else:
        return "hold-card"

def create_confidence_gauge(confidence: float) -> go.Figure:
    """Create a confidence gauge chart"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = confidence * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Confidence Level (%)"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 40], 'color': "lightgray"},
                {'range': [40, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

async def run_kautilya_analysis(user_id: str, symbol: str, sector: str, question: str) -> Dict[str, Any]:
    """
    Run the Kautilya backend analysis asynchronously
    This is equivalent to running: python main.py --user_id X --symbol Y --question Z
    """
    try:
        # Validate symbol
        universe = load_universe("stocks.json")
        if not validate_symbol(symbol, universe):
            raise ValueError(f"Invalid symbol: {symbol} not in NIFTY50 universe")

        # Build initial state (same as main.py)
        initial_state: DecisionState = {
            "user_id": user_id,
            "question": question,
            "symbol": symbol,
            "sector": sector,
            "agent_outputs": {},
            "citations": [],
            "errors": [],
        }

        # Build and run graph (same as main.py)
        graph = build_graph()
        result = await graph.ainvoke(initial_state)

        # Return decision JSON or error fallback
        if "decision_json" in result:
            return result["decision_json"]
        else:
            # Conservative HOLD decision (same as main.py)
            return {
                "decision": "HOLD",
                "confidence": 0.1,
                "horizon": "medium",
                "why": "System error: Failed to generate decision. HOLD recommended as conservative default.",
                "key_factors": ["System processing error"],
                "risks": ["Unable to complete analysis"],
                "personalization_considerations": ["Conservative approach advised"],
                "used_agents": [],
                "citations": [],
            }

    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        return {
            "decision": "HOLD",
            "confidence": 0.1,
            "horizon": "medium",
            "why": f"Analysis error: {str(e)}. HOLD recommended as conservative default.",
            "key_factors": ["System error occurred"],
            "risks": ["Unable to analyze data properly"],
            "personalization_considerations": ["Conservative approach recommended"],
            "used_agents": [],
            "citations": [],
        }

def read_log_file() -> str:
    """Read the latest logs from kautilya.log"""
    try:
        log_file = os.path.join(os.path.dirname(__file__), "kautilya.log")
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Return last 50 lines
                return ''.join(lines[-50:])
        return "No log file found."
    except Exception as e:
        return f"Error reading log file: {e}"

def display_decision_result(result: Dict[str, Any]):
    """Display the decision result in a structured layout"""
    
    # Main decision header
    decision = result.get("decision", "UNKNOWN")
    confidence = result.get("confidence", 0.0)
    horizon = result.get("horizon", "medium")
    
    # Decision summary card
    card_class = get_decision_card_class(decision)
    confidence_class = get_confidence_color(confidence)
    
    st.markdown(f"""
    <div class="decision-card {card_class}" style="color: black;">
        <h2>📊 Investment Decision: {decision}</h2>
        <p><strong>Confidence:</strong> <span class="{confidence_class}">{confidence:.1%}</span></p>
        <p><strong>Investment Horizon:</strong> {horizon.title()}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Explanation section
        st.subheader("💡 Why This Decision?")
        why_text = result.get("why", "No explanation provided")
        if isinstance(why_text, str):
            # Split by bullet points or newlines
            points = [point.strip() for point in why_text.replace("•", "\n").split("\n") if point.strip()]
            for point in points:
                if point:
                    st.write(f"• {point}")
        else:
            st.write(why_text)
    
    with col2:
        # Confidence gauge
        st.subheader("🎯 Confidence Level")
        fig = create_confidence_gauge(confidence)
        st.plotly_chart(fig, use_container_width=True)
    
    # Key factors and risks in two columns
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🔑 Key Factors")
        key_factors = result.get("key_factors", [])
        if key_factors:
            for factor in key_factors:
                st.write(f"✓ {factor}")
        else:
            st.write("No key factors identified")
    
    with col4:
        st.subheader("⚠️ Risks")
        risks = result.get("risks", [])
        if risks:
            for risk in risks:
                st.write(f"⚡ {risk}")
        else:
            st.write("No specific risks identified")
    
    # Personalization insights
    st.subheader("👤 Personalization Insights")
    personalization = result.get("personalization_considerations", [])
    if personalization:
        for insight in personalization:
            st.info(f"💡 {insight}")
    else:
        st.info("No personalized insights available")
    
    # Citations section
    citations = result.get("citations", [])
    if citations:
        st.subheader("📚 Sources & Citations")
        for i, citation in enumerate(citations, 1):
            if citation.startswith("http"):
                st.markdown(f"{i}. [{citation}]({citation})")
            else:
                st.write(f"{i}. {citation}")
    
    # Used agents
    used_agents = result.get("used_agents", [])
    if used_agents:
        st.subheader("🤖 Analysis Components")
        agent_cols = st.columns(min(len(used_agents), 4))
        for i, agent in enumerate(used_agents):
            with agent_cols[i % 4]:
                st.write(f"🔍 {agent.replace('_', ' ').title()}")

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">📈 Kautilya - NIFTY50 Investment Advisor</h1>', unsafe_allow_html=True)
    st.markdown("*Intelligent investment decisions powered by multi-agent analysis*")
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("🔧 Analysis Parameters")
        
        # Load NIFTY50 symbols
        nifty50_symbols = load_nifty50_symbols()
        
        # User inputs
        user_id = st.text_input(
            "👤 User ID",
            value="demo_user",
            help="Enter your unique user identifier"
        )
        
        symbol = st.selectbox(
            "📊 NIFTY50 Symbol",
            options=nifty50_symbols,
            index=0 if nifty50_symbols else None,
            help="Select a NIFTY50 company for analysis"
        )
        
        # Sector mapping (simplified)
        sector_mapping = {
            "Reliance Industries": "Energy",
            "HDFC Bank": "Banking",
            "Bharti Airtel": "Telecom",
            "Tata Consultancy Services": "IT",
            "ICICI Bank": "Banking",
            "State Bank of India": "Banking",
            "Bajaj Finance": "Financial Services",
            "Infosys": "IT",
            "Hindustan Unilever": "FMCG",
            "ITC": "FMCG",
            "Larsen & Toubro": "Infrastructure",
            "Maruti Suzuki": "Automotive",
            "Mahindra & Mahindra": "Automotive",
            "Kotak Bank": "Banking",
            "Sun Pharmaceutical": "Pharma",
            "HCL Technologies": "IT",
            "UltraTech Cement": "Cement",
            "Axis Bank": "Banking",
            "Bajaj Finserv": "Financial Services",
        }
        
        sector = st.text_input(
            "🏭 Sector (Optional)",
            value=sector_mapping.get(symbol, ""),
            help="Industry sector of the selected company"
        )
        
        question = st.text_area(
            "❓ Investment Question",
            value="Should I invest in this stock for the next 6 months?",
            height=100,
            help="Describe your investment query or scenario"
        )
        
        # Analysis button
        analyze_button = st.button(
            "🚀 Analyze Investment",
            type="primary",
            disabled=st.session_state.processing,
            use_container_width=True
        )
        
        # Settings
        st.header("⚙️ Settings")
        show_raw_json = st.checkbox("Show Raw JSON Output", value=False)
        show_logs = st.checkbox("Show System Logs", value=False)
    
    # Main content area
    if analyze_button and not st.session_state.processing:
        if not all([user_id, symbol, question]):
            st.error("Please fill in all required fields (User ID, Symbol, Question)")
            return
        
        st.session_state.processing = True
        st.session_state.decision_result = None
        
        # Show processing status
        with st.spinner("🔄 Running multi-agent analysis..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Update progress
                status_text.text("🔍 Loading personal context...")
                progress_bar.progress(20)
                
                status_text.text("🤖 Gathering signals from 15+ agents...")
                progress_bar.progress(40)
                
                status_text.text("🧠 Processing with LLM...")
                progress_bar.progress(70)
                
                # Run the actual analysis
                result = asyncio.run(run_kautilya_analysis(user_id, symbol, sector, question))
                
                status_text.text("✅ Analysis complete!")
                progress_bar.progress(100)
                
                st.session_state.decision_result = result
                st.session_state.processing = False
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                st.success("Analysis completed successfully!")
                
            except Exception as e:
                st.session_state.processing = False
                progress_bar.empty()
                status_text.empty()
                st.error(f"Analysis failed: {str(e)}")
                return
    
    # Display results
    if st.session_state.decision_result:
        st.markdown("---")
        display_decision_result(st.session_state.decision_result)
        
        # Raw JSON toggle
        if show_raw_json:
            st.subheader("🔧 Raw JSON Output")
            st.json(st.session_state.decision_result)
    
    # Logs section
    if show_logs:
        st.markdown("---")
        st.subheader("📋 System Logs")
        with st.expander("View Latest Logs", expanded=False):
            logs = read_log_file()
            st.text(logs)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "*Kautilya uses advanced multi-agent systems to analyze macroeconomic, "
        "company-specific, and policy factors for informed investment decisions.*"
    )

if __name__ == "__main__":
    main()
