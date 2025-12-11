import streamlit as st
import os
from datetime import datetime
from utils.rag_helper import RAGAnalyzer
from utils.database_utils import save_analysis, get_all_contracts
from utils.email_notifier import EmailNotifier
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json


# Helper function for amendment recommendations
def generate_amendment_recommendation(issue_title):
    """Generate amendment recommendations based on issue"""
    recommendations = {
        "Equal Employment Opportunity": "**Suggested Text:** \"Employer is committed to Equal Employment Opportunity and does not discriminate based on race, color, religion, sex, national origin, age, disability, or any other protected characteristic.\"",
        "Employee Handbook": "**Suggested Text:** \"Employee shall receive a copy of the Employee Handbook within 3 business days of employment. All policies contained therein are incorporated by reference into this Agreement.\"",
        "Benefits": "**Suggested Text:** \"Employee is entitled to all benefits offered by Employer, including but not limited to health insurance, retirement plans, and paid time off, as outlined in the Employee Handbook.\"",
        "Workplace Safety": "**Suggested Text:** \"Employer is committed to providing a safe workplace and shall comply with all OSHA and applicable state/local safety regulations.\"",
        "Data Protection": "**Suggested Text:** \"Employer shall protect Employee's personal data in accordance with applicable data protection laws and shall not disclose such data to third parties without Employee's consent.\"",
        "Harassment": "**Suggested Text:** \"Employer has zero tolerance for harassment or discrimination. Employees may report concerns to HR. All reports shall be investigated promptly and confidentially.\"",
        "Termination": "**Suggested Text:** \"Termination shall comply with all applicable laws and shall provide appropriate notice period as per local labor laws.\"",
    }
    
    for key, value in recommendations.items():
        if key.lower() in issue_title.lower():
            return value
    
    return "**Recommended Action:** Review this clause against current regulatory standards and industry best practices."

# Page configuration
st.set_page_config(
    page_title="Contract Compliance Analyzer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'uploaded_contracts' not in st.session_state:
    st.session_state.uploaded_contracts = []
if 'current_contract' not in st.session_state:
    st.session_state.current_contract = None

# Sidebar navigation
st.sidebar.title("🔐 Contract Compliance Analyzer")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate to:",
    ["🏠 Home", "📤 Upload Contract", "📊 Risk Analysis", "✅ Clauses & Amendments", "💬 Chatbot", "⚙️ Settings"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 Tip: Upload a contract to get started with compliance analysis")

# Main content
if page == "🏠 Home":
    st.markdown("<h1 class='main-header'>📋 Contract Compliance Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("### Welcome to Your Compliance Management System")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Contracts Analyzed", 1, "Contract_v1.pdf")
    
    with col2:
        st.metric("Average Risk Score", "Medium", "⚠️")
    
    with col3:
        st.metric("Last Analysis", "Today")
    
    st.markdown("---")
    st.markdown("### 📌 Quick Start Guide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### Step 1: Upload Contract
        - Go to **📤 Upload Contract** page
        - Upload your PDF or text file
        - System will extract and analyze it
        """)
    
    with col2:
        st.markdown("""
        #### Step 2: Review Analysis
        - Check **📊 Risk Analysis** for compliance issues
        - View **✅ Clauses & Amendments** for recommendations
        - Ask questions in **💬 Chatbot**
        """)
    
    st.markdown("---")
    st.markdown("### 🎯 Features")
    
    features = {
        "🔍 RAG-based Analysis": "Uses AI to analyze contracts against compliance standards",
        "📊 Risk Visualization": "Beautiful charts and dashboards showing compliance issues",
        "💡 Smart Recommendations": "AI-powered suggestions for contract improvements",
        "💬 Interactive Chatbot": "Ask questions about your contract and regulations",
        "📈 History Tracking": "Keep track of all analyzed contracts"
    }
    
    for feature, description in features.items():
        st.write(f"**{feature}**: {description}")
    
    st.markdown("---")
    st.info("ℹ️ **Rate Limiting Info**: This app uses Groq's free API tier with token limits. Responses are cached to minimize API calls. If you hit rate limits, wait a few minutes and try again.")

elif page == "📤 Upload Contract":
    st.markdown("### 📤 Upload Contract for Analysis")
    st.info("Upload a contract file (PDF or TXT) to analyze it for compliance issues")
    
    # Email notification configuration
    st.markdown("---")
    st.markdown("#### 📧 Email Notifications (Optional)")
    
    email_notifier = EmailNotifier()
    
    if email_notifier.is_email_enabled():
        st.success("✅ Email notifications are configured")
        st.write("Enter your email address to receive analysis results:")
        
        notification_email = st.text_input(
            "Recipient Email",
            value=st.session_state.get('notification_email', ''),
            placeholder="your.email@example.com",
            key="email_input"
        )
        
        if notification_email:
            st.session_state['notification_email'] = notification_email
            st.caption(f"📧 Notifications will be sent to: {notification_email}")
    else:
        st.warning("⚠️ Email notifications not configured")
        st.info("""
        To enable email notifications, add these to your `.env` file:
        ```
        EMAIL_SENDER=your_email@gmail.com
        EMAIL_PASSWORD=your_app_password
        EMAIL_SMTP_SERVER=smtp.gmail.com
        EMAIL_SMTP_PORT=587
        EMAIL_SENDER_NAME=Contract Analyzer
        ```
        """)
    
    st.markdown("---")
    
    # Initialize RAG analyzer
    @st.cache_resource
    def get_rag_analyzer():
        analyzer = RAGAnalyzer()
        analyzer.setup()
        return analyzer
    
    try:
        analyzer = get_rag_analyzer()
    except Exception as e:
        st.error(f"Error initializing RAG system: {str(e)}")
        analyzer = None
    
    # Simple file uploader without extra features
    uploaded_file = st.file_uploader(
        "Select a contract file (PDF or TXT)",
        type=["pdf", "txt"],
        accept_multiple_files=False
    )
    
    if uploaded_file is not None:
        try:
            st.success(f"✅ Selected: {uploaded_file.name}")
            
            # Create uploads directory
            os.makedirs("data/uploads", exist_ok=True)
            
            # Save file directly
            file_path = f"data/uploads/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())
            
            st.info(f"File saved successfully")
            
            # Store in session
            st.session_state.current_contract = {
                'name': uploaded_file.name,
                'path': file_path,
                'size': len(uploaded_file.getvalue()),
                'uploaded_at': datetime.now()
            }
            
            st.markdown("---")
            
            # Analyze button
            if st.button("🔍 Analyze This Contract", use_container_width=True):
                if analyzer is None:
                    st.error("❌ RAG system error. Check your setup.")
                else:
                    progress = st.progress(0)
                    status = st.empty()
                    
                    try:
                        status.text("📖 Loading contract...")
                        progress.progress(20)
                        
                        contract_text = analyzer.load_contract(file_path)
                        st.session_state.current_contract['text'] = contract_text
                        
                        status.text("🔍 Analyzing compliance...")
                        progress.progress(50)
                        
                        analysis_result = analyzer.analyze_contract(contract_text)
                        st.session_state.current_analysis = analysis_result
                        
                        status.text("💾 Saving results...")
                        progress.progress(80)
                        
                        save_analysis(uploaded_file.name, file_path, {
                            'clauses': analysis_result.get('key_clauses', []),
                            'issues': analysis_result.get('compliance_issues', [])
                        })
                        
                        progress.progress(100)
                        status.text("✅ Analysis complete!")
                        
                        # Send email notification in background (non-blocking)
                        if st.session_state.get('notification_email'):
                            try:
                                email_notifier = EmailNotifier()
                                if email_notifier.is_email_enabled():
                                    email_notifier.send_notification_safe(
                                        st.session_state['notification_email'],
                                        uploaded_file.name,
                                        analysis_result
                                    )
                            except:
                                pass  # Silently fail to not block UI
                        
                        st.balloons()
                        st.success("✅ Successfully analyzed! Check other pages for results.")
                        
                        # Quick summary
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Clauses", len(analysis_result.get('key_clauses', [])))
                        with col2:
                            st.metric("Issues", len(analysis_result.get('compliance_issues', [])))
                        with col3:
                            issues = analysis_result.get('compliance_issues', [])
                            high = len([i for i in issues if i.get('risk_level') == 'High'])
                            st.metric("High Risk", high)
                        
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    else:
        st.markdown("---")
        st.info("👆 Click 'Browse files' above to select a contract")
        
        st.markdown("### 📚 Available Test Contracts:")
        
        test_files = [
            ("data/contracts/Contract_v1.pdf", "Employee Contract (Sample)"),
        ]
        
        for filepath, description in test_files:
            if os.path.exists(filepath):
                st.write(f"✅ **{description}** - Ready to test")
            else:
                st.write(f"❌ **{description}** - Not found")

elif page == "📊 Risk Analysis":
    st.markdown("### 📊 Risk Analysis Dashboard")
    
    if st.session_state.current_contract is None or 'current_analysis' not in st.session_state:
        st.warning("⚠️ No contract analyzed yet. Please upload and analyze a contract first!")
        
        # Show option to select from history
        st.markdown("### 📜 Or select from analysis history:")
        contracts = get_all_contracts()
        if contracts:
            selected = st.selectbox("Previously analyzed contracts:", [c['filename'] for c in contracts])
            st.info(f"Selected: {selected} (uploaded on {contracts[0]['upload_date']})")
        else:
            st.info("No contracts analyzed yet.")
    else:
        analysis = st.session_state.current_analysis
        contract_name = st.session_state.current_contract['name']
        
        st.success(f"✅ Analysis: {contract_name}")
        
        # Get issues
        issues = analysis.get('compliance_issues', [])
        
        if not issues:
            st.info("No compliance issues found!")
        else:
            # Top metrics
            col1, col2, col3, col4 = st.columns(4)
            
            high_risk = len([i for i in issues if i.get('risk_level') == 'High'])
            medium_risk = len([i for i in issues if i.get('risk_level') == 'Medium'])
            low_risk = len([i for i in issues if i.get('risk_level') == 'Low'])
            
            with col1:
                st.metric("Total Issues", len(issues))
            with col2:
                st.metric("🔴 High Risk", high_risk)
            with col3:
                st.metric("🟡 Medium Risk", medium_risk)
            with col4:
                st.metric("🟢 Low Risk", low_risk)
            
            st.markdown("---")
            
            # Risk distribution pie chart
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Risk Distribution")
                risk_counts = {'High': high_risk, 'Medium': medium_risk, 'Low': low_risk}
                risk_df = pd.DataFrame(list(risk_counts.items()), columns=['Risk Level', 'Count'])
                
                fig = px.pie(risk_df, values='Count', names='Risk Level', 
                            color='Risk Level',
                            color_discrete_map={'High': '#d62728', 'Medium': '#ff7f0e', 'Low': '#2ca02c'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### Compliance Score")
                # Calculate compliance score
                score = max(0, 100 - (high_risk * 30 + medium_risk * 15 + low_risk * 5))
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Compliance Score"},
                    delta = {'reference': 80},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 33], 'color': "lightgray"},
                            {'range': [33, 66], 'color': "gray"}],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 50}}))
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Detailed issues table
            st.markdown("#### Detailed Compliance Issues")
            
            # Create color map for risk levels
            def get_risk_color(risk_level):
                colors = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}
                return colors.get(risk_level, '⚪')
            
            for idx, issue in enumerate(issues, 1):
                with st.expander(f"{get_risk_color(issue.get('risk_level'))} {issue.get('title', 'Issue')} ({issue.get('risk_level')} Risk)"):
                    st.write(f"**Reason:** {issue.get('reason', 'N/A')}")
            
            st.markdown("---")
            st.markdown("### 📥 Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Generate PDF Report"):
                    st.info("PDF export feature coming soon!")
            
            with col2:
                if st.button("📋 Download CSV"):
                    csv_data = pd.DataFrame(issues)
                    st.download_button(
                        label="Click to download CSV",
                        data=csv_data.to_csv(index=False),
                        file_name=f"compliance_report_{contract_name}.csv",
                        mime="text/csv"
                    )

elif page == "✅ Clauses & Amendments":
    st.markdown("### ✅ Key Clauses & Amendment Recommendations")
    
    if st.session_state.current_contract is None or 'current_analysis' not in st.session_state:
        st.warning("⚠️ No contract analyzed yet. Please upload and analyze a contract first!")
    else:
        analysis = st.session_state.current_analysis
        contract_name = st.session_state.current_contract['name']
        
        st.success(f"✅ Analysis: {contract_name}")
        
        # Get clauses
        clauses = analysis.get('key_clauses', [])
        issues = analysis.get('compliance_issues', [])
        
        st.markdown("#### 📄 Key Clauses Found")
        
        if clauses:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Total Clauses Identified: {len(clauses)}**")
            
            for clause in clauses:
                st.markdown(f"✓ {clause}")
        else:
            st.info("No specific clauses extracted.")
        
        st.markdown("---")
        st.markdown("#### 🔄 Recommended Amendments")
        
        if issues:
            st.info(f"Based on {len(issues)} compliance issues found, here are recommended amendments:")
            
            for issue in issues:
                if issue.get('risk_level') in ['High', 'Medium']:
                    with st.expander(f"📝 {issue.get('title')} ({issue.get('risk_level')} Risk)"):
                        st.write(f"**Issue:** {issue.get('reason')}")
                        st.write("\n**Recommended Amendment:**")
                        
                        # Generate recommendations based on issue type
                        recommendations = generate_amendment_recommendation(issue.get('title'))
                        st.markdown(recommendations)
        else:
            st.success("✅ No amendments needed!")
        
        st.markdown("---")
        st.markdown("#### 📋 Regulatory Updates")
        
        # Check for regulatory updates
        if os.path.exists("data/regulations.json"):
            st.info("Checking regulations.json for updates...")
            import json
            try:
                with open("data/regulations.json", "r") as f:
                    regulations = json.load(f)
                
                st.write("**Latest Regulatory Changes:**")
                if isinstance(regulations, dict):
                    for key, value in regulations.items():
                        st.write(f"• {key}: {value}")
                else:
                    st.write(regulations)
            except Exception as e:
                st.warning(f"Could not load regulations: {str(e)}")
        else:
            st.info("📄 regulations.json file not found")

elif page == "💬 Chatbot":
    st.markdown("### 💬 Contract Compliance Chatbot")
    
    if st.session_state.current_contract is None or 'current_analysis' not in st.session_state:
        st.warning("⚠️ No contract loaded. Please upload and analyze a contract first!")
        st.info("Once you analyze a contract, you can ask questions about it here.")
    else:
        contract_name = st.session_state.current_contract['name']
        st.success(f"💬 Chatting about: {contract_name}")
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Initialize RAG analyzer for chatbot
        @st.cache_resource
        def get_chatbot_analyzer():
            analyzer = RAGAnalyzer()
            analyzer.setup()
            return analyzer
        
        try:
            analyzer = get_chatbot_analyzer()
        except Exception as e:
            st.error(f"Error initializing chatbot: {str(e)}")
            analyzer = None
        
        # Display chat history
        st.markdown("#### 💬 Conversation")
        
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f"**🙋 You:** {message['content']}")
                else:
                    st.markdown(f"**🤖 Assistant:** {message['content']}")
        
        # User input
        st.markdown("---")
        st.markdown("#### ❓ Ask a Question")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_question = st.text_input("Ask about the contract, compliance, or regulations:", placeholder="e.g., What are the confidentiality clauses?")
        
        with col2:
            send_button = st.button("📤 Send", key="send_btn")
        
        if send_button and user_question:
            if analyzer is None:
                st.error("Chatbot not initialized. Please check your setup.")
            else:
                # Add user message to history
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': user_question
                })
                
                # Get bot response with rate limit handling
                with st.spinner("🤔 Thinking..."):
                    try:
                        contract_text = st.session_state.current_contract.get('text', '')
                        
                        if not contract_text:
                            # Load contract text if not in session
                            contract_path = st.session_state.current_contract.get('path', '')
                            if contract_path:
                                contract_text = analyzer.load_contract(contract_path)
                                st.session_state.current_contract['text'] = contract_text
                        
                        response = analyzer.get_chatbot_response(contract_text, user_question)
                        
                        # Check for rate limit fallback
                        if "Unable to process due to API rate limits" in response:
                            st.warning("⚠️ " + response)
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': "The API is rate-limited. Please wait a few minutes and try again."
                            })
                        else:
                            # Add bot response to history
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': response
                            })
                            st.success("✅ Response generated!")
                        
                        st.rerun()
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "429" in error_msg or "rate_limit" in error_msg.lower():
                            st.error("⚠️ Rate limit exceeded. The app is using too many tokens. Please try again in a few minutes.")
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': "⚠️ Rate limit reached. Please wait and try again later."
                            })
                        else:
                            st.error(f"Error: {error_msg}")
        
        # Quick question suggestions
        st.markdown("---")
        st.markdown("#### 💡 Suggested Questions")
        
        suggestions = [
            "What are the confidentiality and NDA clauses?",
            "What are the termination conditions and notice periods?",
            "Are there any non-compete or non-solicitation clauses?",
            "What benefits and compensations are mentioned?",
            "What are the working hours and leave policies?",
            "Are there any compliance gaps based on current regulations?"
        ]
        
        cols = st.columns(2)
        for idx, suggestion in enumerate(suggestions):
            with cols[idx % 2]:
                if st.button(f"💬 {suggestion}", key=f"suggest_{idx}"):
                    st.session_state.chat_history.append({
                        'role': 'user',
                        'content': suggestion
                    })
                    
                    if analyzer is not None:
                        with st.spinner("🤔 Thinking..."):
                            try:
                                contract_text = st.session_state.current_contract.get('text', '')
                                
                                if not contract_text:
                                    contract_path = st.session_state.current_contract.get('path', '')
                                    if contract_path:
                                        contract_text = analyzer.load_contract(contract_path)
                                        st.session_state.current_contract['text'] = contract_text
                                
                                response = analyzer.get_chatbot_response(contract_text, suggestion)
                                
                                # Check for rate limit fallback
                                if "Unable to process due to API rate limits" in response:
                                    st.warning("⚠️ Rate limit reached")
                                    st.session_state.chat_history.append({
                                        'role': 'assistant',
                                        'content': "⚠️ Rate limit reached. Please try again in a few minutes."
                                    })
                                else:
                                    st.session_state.chat_history.append({
                                        'role': 'assistant',
                                        'content': response
                                    })
                                
                                st.rerun()
                                
                            except Exception as e:
                                error_msg = str(e)
                                if "429" in error_msg or "rate_limit" in error_msg.lower():
                                    st.error("⚠️ Rate limit exceeded")
                                    st.session_state.chat_history.append({
                                        'role': 'assistant',
                                        'content': "⚠️ Rate limit reached. Please wait and try again."
                                    })
                                else:
                                    st.error(f"Error: {error_msg}")
        
        # Clear chat history button
        st.markdown("---")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

elif page == "⚙️ Settings":
    st.markdown("### ⚙️ Settings & Configuration")
    
    # Email Configuration Section
    st.markdown("#### 📧 Email Notification Settings")
    
    email_notifier = EmailNotifier()
    
    if email_notifier.is_email_enabled():
        st.success("✅ Email notifications are configured")
        st.write(f"**Sender:** {email_notifier.sender_email}")
        st.write(f"**SMTP Server:** {email_notifier.smtp_server}:{email_notifier.smtp_port}")
        
        st.markdown("---")
        st.markdown("#### 📧 Test Email Notification")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            test_email = st.text_input(
                "Test Email Address",
                placeholder="test@example.com",
                key="test_email_input"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            test_button = st.button("📤 Send Test Email", use_container_width=True)
        
        if test_button and test_email:
            with st.spinner("📧 Sending test email..."):
                # Create sample analysis result for testing
                sample_analysis = {
                    'key_clauses': [
                        'Confidentiality Clause',
                        'Non-Compete Agreement',
                        'Intellectual Property Rights',
                        'Termination Conditions',
                        'Dispute Resolution'
                    ],
                    'compliance_issues': [
                        {
                            'title': 'Missing Data Protection Clause',
                            'risk_level': 'High',
                            'reason': 'Contract does not include GDPR/CCPA compliance language'
                        },
                        {
                            'title': 'Vague Termination Clause',
                            'risk_level': 'Medium',
                            'reason': 'Notice period is not clearly specified'
                        },
                        {
                            'title': 'Outdated Compliance Reference',
                            'risk_level': 'Low',
                            'reason': 'References old regulatory standards'
                        }
                    ]
                }
                
                success, message = email_notifier.send_notification(
                    test_email,
                    "Test Contract (Sample)",
                    sample_analysis,
                    test_mode=False
                )
                
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    else:
        st.warning("⚠️ Email notifications not configured")
        
        st.markdown("#### 🔧 Setup Instructions")
        
        st.markdown("""
        To enable email notifications, follow these steps:
        
        **Step 1: Choose Email Provider**
        - Gmail (recommended for development)
        - SendGrid, Mailgun, or other SMTP provider
        
        **Step 2: Configure Gmail (if using Gmail)**
        1. Enable 2-factor authentication on your Google account
        2. Generate an App Password at: https://myaccount.google.com/apppasswords
        3. Copy the generated 16-character password
        
        **Step 3: Update `.env` File**
        
        Create or update `.env` in your project root with:
        
        ```
        # Email Configuration
        EMAIL_SENDER=your_email@gmail.com
        EMAIL_PASSWORD=your_app_password_16chars
        EMAIL_SMTP_SERVER=smtp.gmail.com
        EMAIL_SMTP_PORT=587
        EMAIL_SENDER_NAME=Contract Analyzer
        ```
        
        **Step 4: Restart the App**
        
        Restart Streamlit for changes to take effect.
        """)
        
        st.markdown("#### 📚 Using Other Email Providers")
        
        providers = {
            "Gmail": {
                "SMTP": "smtp.gmail.com",
                "Port": "587",
                "Notes": "Requires App Password"
            },
            "Outlook/Hotmail": {
                "SMTP": "smtp-mail.outlook.com",
                "Port": "587",
                "Notes": "Use your email and password"
            },
            "Yahoo Mail": {
                "SMTP": "smtp.mail.yahoo.com",
                "Port": "587",
                "Notes": "Requires App Password"
            },
            "SendGrid": {
                "SMTP": "smtp.sendgrid.net",
                "Port": "587",
                "Notes": "Use 'apikey' as username, API key as password"
            }
        }
        
        for provider, config in providers.items():
            with st.expander(f"📧 {provider}"):
                st.write(f"**SMTP Server:** {config['SMTP']}")
                st.write(f"**Port:** {config['Port']}")
                st.write(f"**Notes:** {config['Notes']}")
    
    st.markdown("---")
    st.markdown("#### 📊 About This App")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("RAG System", "Active")
    
    with col2:
        st.metric("Cache DB", "Active")
    
    with col3:
        email_status = "✅ Configured" if email_notifier.is_email_enabled() else "❌ Not Configured"
        st.write(f"**Email Notifications:** {email_status}")
    
    st.markdown("---")
    st.markdown("#### 🆘 Support")
    
    st.write("""
    - **Documentation:** See TOKEN_OPTIMIZATION_GUIDE.md
    - **Issues:** Check logs for error messages
    - **Reset:** Delete `response_cache.db` to clear cache
    """)

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>© 2025 Infosys Springboard Project | Powered by Groq LLM</p>", unsafe_allow_html=True)
