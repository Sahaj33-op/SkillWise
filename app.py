import streamlit as st
import tempfile
import os
import json
import re
import time
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from resume_parser import parse_resume
from roadmap_generator import generate_roadmap
from goal_analyzer import analyze_goals
import google.generativeai as genai

def update_progress(progress_bar, eta_placeholder, current_progress, total_stages, start_time, estimated_time, stage_name):
    """Update progress bar with current stage information."""
    progress = (current_progress / total_stages) * 100
    elapsed = time.time() - start_time
    eta = max(0, estimated_time - elapsed)
    progress_bar.progress(int(progress))
    eta_placeholder.text(f"⏳ {stage_name}... {int(progress)}%")

# Configure Streamlit page
st.set_page_config(page_title="SkillWise", page_icon="💡", layout="wide", initial_sidebar_state="expanded")

# Load external CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Additional custom styles
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

.stApp {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Roboto', sans-serif;
}
h1, h2, h3, h4, h5, h6 {
    color: #ffffff;
    font-weight: 500;
}
.stTextInput input, .stSelectbox div, .stTextArea textarea {
    background-color: #2d2d44 !important;
    color: #e0e0e0 !important;
    border: none !important;
    border-radius: 8px;
    transition: border-color 0.3s ease;
}
.stTextInput input:focus, .stSelectbox div:focus, .stTextArea textarea:focus {
    border: none !important;
    box-shadow: 0 0 5px rgba(96, 165, 250, 0.5) !important;
}
div[data-testid="stFileUploaderDropzone"] {
    background-color: #3b3b5a !important;
    border: 2px dashed #60a5fa !important;
    color: #e0e0e0 !important;
    border-radius: 8px;
}
div[data-testid="stTabs"] button {
    background-color: #2d2d44;
    color: #e0e0e0;
    border-radius: 8px 8px 0 0;
    transition: background-color 0.3s ease;
}
div[data-testid="stTabs"] button:hover {
    background-color: #4a69bd;
}
div[data-testid="stTabs"] button p {
    font-size: 18px !important;
    font-weight: 500 !important;
}
div[data-testid="stTab"] {
    background-color: none;
    padding: 20px;
    border-radius: 8px;
}
.stProgress .st-bo {
    background-color: #4a69bd !important;
}
.stProgress .st-bo > div {
    background-color: #60a5fa !important;
}
.stCheckbox label p {
    font-size: 14px !important;
    color: #e0e0e0;
}
.footer {
    background-color: #2d2d44;
    padding: 20px;
    text-align: center;
    border-top: 1px solid #4a69bd;
    margin-top: 40px;
    border-radius: 8px;
}
.footer p {
    margin: 10px 0;
    font-size: 14px;
    color: #b0b0b0;
}
.footer a {
    color: #4a69bd;
    text-decoration: none;
    margin: 0 10px;
    transition: color 0.3s ease;
}
.footer a:hover {
    color: #60a5fa;
}
.social-icons a {
    margin: 0 15px;
    font-size: 20px;
    color: #b0b0b0;
    transition: color 0.3s ease;
}
.social-icons a:hover {
    color: #60a5fa;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.stMarkdown, .stSuccess, .stInfo, .stWarning, .stError {
    animation: fadeIn 0.5s ease-in-out;
}
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
""", unsafe_allow_html=True)

# Initialize session state
if "roadmap" not in st.session_state:
    st.session_state.roadmap = ""
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "parsed_resume" not in st.session_state:
    st.session_state.parsed_resume = None
if "goal" not in st.session_state:
    st.session_state.goal = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "custom_role" not in st.session_state:
    st.session_state.custom_role = ""
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
if "progress" not in st.session_state:
    st.session_state.progress = {}
if "editing_section" not in st.session_state:
    st.session_state.editing_section = None
if "generation_time" not in st.session_state:
    st.session_state.generation_time = 10.0
if "first_visit" not in st.session_state:
    st.session_state.first_visit = True
if "survey_submitted" not in st.session_state:
    st.session_state.survey_submitted = False
if "resume_upload_time" not in st.session_state:
    st.session_state.resume_upload_time = 5.0
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# Onboarding Walkthrough for first-time users
if st.session_state.first_visit:
    st.info("""
    ### Welcome to SkillWise! 🎉
    Follow these steps to get started:
    1. **Enter your Gemini API Key** in the sidebar (⚙️ Configuration).
    2. **Upload your resume** in the Resume tab (📄 Upload Your Resume).
    3. **Select your career goal and role** (e.g., AI Engineer).
    4. Click **Generate Roadmap** to create your personalized learning path.
    5. Explore your roadmap in the Roadmap tab (🗺️).
    """)
    st.session_state.first_visit = False

# Load progress from file
def load_progress():
    if os.path.exists("progress.json"):
        with open("progress.json", "r") as f:
            st.session_state.progress = json.load(f)

# Save progress to file
def save_progress():
    with open("progress.json", "w") as f:
        json.dump(st.session_state.progress, f)

# Handle Gemini API key with Submit button and Change option
with st.sidebar:
    st.header("⚙️ Configuration")
    if not st.session_state.gemini_api_key:
        st.warning("⚠️ Gemini API key not found. Please enter it below.")
        api_key_input = st.text_input("Enter Gemini API Key", type="password")
        if st.button("Submit"):
            if api_key_input:
                st.session_state.gemini_api_key = api_key_input
                genai.configure(api_key=api_key_input)
                st.success("✅ API Key submitted!")
            else:
                st.error("❌ Please enter a valid API key.")
    else:
        st.success("✅ API Key is set!")
        if st.button("🔄 Change API Key"):
            st.session_state.gemini_api_key = ""
            st.rerun()

st.title("🧠 SkillWise: AI-Powered Learning Path Generator")

# Tabs
tab1, tab2 = st.tabs(["Resume", "Roadmap"])

# Resume Tab
with tab1:
    st.subheader("🎯 Select Career Goal")
    st.session_state.goal = st.text_input("What role are you targeting?", placeholder="e.g., AI Developer, Product Manager", value=st.session_state.goal)
    if st.session_state.goal.strip():
        goal_analysis = analyze_goals(st.session_state.goal)
        st.markdown(goal_analysis)
    st.subheader("📚 Select Tech Role")
    roles = [
        "Select a tech role",
        "AI Engineer",
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "Product Manager",
        "Data Analyst",
        "Cybersecurity Expert",
        "DevOps Engineer",
        "UI/UX Designer",
        "Machine Learning Engineer",
        "Blockchain Developer",
        "Cloud Architect",
        "Data Scientist",
        "Software Engineer",
        "Mobile App Developer",
        "Other"
    ]
    st.session_state.role = st.selectbox("Choose a role", roles, index=roles.index(st.session_state.role) if st.session_state.role in roles else 0)
    if st.session_state.role == "Other":
        st.session_state.custom_role = st.text_input("Please specify your role", placeholder="e.g., Game Developer", value=st.session_state.custom_role)
    effective_role = st.session_state.custom_role if st.session_state.role == "Other" and st.session_state.custom_role else st.session_state.role
    st.subheader("📄 Upload Your Resume")
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")
    
    if uploaded_file is not None and not st.session_state.is_processing:
        st.session_state.is_processing = True
        progress_bar = st.progress(0)
        eta_placeholder = st.empty()
        start_time = time.time()
        
        try:
            # Stage 1: Validating and Uploading
            update_progress(progress_bar, eta_placeholder, 0, 100, start_time, st.session_state.resume_upload_time, "Processing Resume")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name
            
            # Stage 2: Parsing
            update_progress(progress_bar, eta_placeholder, 50, 100, start_time, st.session_state.resume_upload_time, "Processing Resume")
            parsed_text = parse_resume(tmp_path)
            
            if len(parsed_text.strip()) > 20:
                st.session_state.parsed_resume = parsed_text
                st.session_state.resume_text = parsed_text
                st.success("✅ Resume uploaded and processed successfully!")
            else:
                st.error("⚠️ Failed to extract meaningful content. Try another resume.")
                
        except Exception as e:
            st.error(f"❌ Error processing resume: {str(e)}")
        finally:
            try:
                os.remove(tmp_path)
            except:
                pass
            progress_bar.empty()
            eta_placeholder.empty()
            st.session_state.is_processing = False
            
            # Update estimated time for future uploads
            total_time = time.time() - start_time
            st.session_state.resume_upload_time = total_time

    if st.button("🚀 Generate Roadmap") and not st.session_state.is_processing:
        if not st.session_state.parsed_resume:
            st.warning("⚠️ Please upload a resume.")
        elif effective_role == "Select a tech role":
            st.warning("⚠️ Please select a valid role.")
        elif st.session_state.role == "Other" and not st.session_state.custom_role.strip():
            st.warning("⚠️ Please specify a role in the text field.")
        elif not st.session_state.gemini_api_key:
            st.error("❌ Please enter a Gemini API key in the sidebar.")
        else:
            st.session_state.is_processing = True
            progress_bar = st.progress(0)
            eta_placeholder = st.empty()
            start_time = time.time()
            
            try:
                # Configure API
                genai.configure(api_key=st.session_state.gemini_api_key)
                
                # Generate prompt
                prompt = (
                    f"Create a personalized learning roadmap to help the user achieve their career goal of becoming a {effective_role} "
                    f"with the specific aspiration: '{st.session_state.goal}'. "
                    f"Based on the role of {effective_role}, identify the key skills and knowledge areas required, "
                    f"and focus on bridging the gaps between the user's current skills and the role's requirements. "
                    f"Provide a step-by-step roadmap with actionable learning steps, including specific resources (e.g., courses, tutorials) "
                    f"and tag each resource with relevant labels (e.g., 'YouTube', 'Beginner-Friendly', 'Coursera') in the format: "
                    f"'* <step> - <tag1>, <tag2>'. Ensure the roadmap is practical and tailored to the user's goal and role."
                )
                
                # Update progress
                update_progress(progress_bar, eta_placeholder, 0, 100, start_time, st.session_state.generation_time, "Generating Roadmap")
                
                # Generate roadmap
                st.session_state.roadmap = generate_roadmap(prompt)
                
                # Update final progress
                update_progress(progress_bar, eta_placeholder, 100, 100, start_time, st.session_state.generation_time, "Complete")
                
                # Update generation time
                actual_time = time.time() - start_time
                st.session_state.generation_time = actual_time
                
                st.success("✅ Roadmap generated! Check it in the Roadmap tab.")
                
            except Exception as e:
                st.error(f"❌ Error generating roadmap: {str(e)}")
            finally:
                progress_bar.empty()
                eta_placeholder.empty()
                st.session_state.is_processing = False

# Roadmap Tab
with tab2:
    if st.session_state.roadmap:
        st.header("🗺️ Your AI-Powered Learning Roadmap")
        required_skills = {
            "AI Engineer": ["Python", "Machine Learning", "TensorFlow", "NLP"],
            "Frontend Developer": ["HTML", "CSS", "JavaScript", "React"],
            "Backend Developer": ["Python", "Node.js", "SQL", "REST APIs"],
            "Full Stack Developer": ["HTML", "JavaScript", "Node.js", "SQL"],
            "Product Manager": ["Agile", "SQL", "Figma", "Jira"],
            "Data Analyst": ["SQL", "Excel", "Tableau", "Python"],
            "Cybersecurity Expert": ["Networking", "Penetration Testing", "Cryptography", "Linux"],
            "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "CI/CD"],
            "UI/UX Designer": ["Figma", "Adobe XD", "User Research", "Prototyping"],
            "Machine Learning Engineer": ["Python", "TensorFlow", "Scikit-learn", "Deep Learning"],
            "Blockchain Developer": ["Solidity", "Ethereum", "Smart Contracts", "Cryptography"],
            "Cloud Architect": ["AWS", "Azure", "GCP", "Terraform"],
            "Data Scientist": ["Python", "R", "Machine Learning", "Statistics"],
            "Software Engineer": ["Java", "Python", "Git", "Algorithms"],
            "Mobile App Developer": ["Swift", "Kotlin", "React Native", "Flutter"]
        }
        default_skills = ["Python", "Git", "Problem Solving", "Communication"]
        skills_to_check = required_skills.get(effective_role, default_skills)
        if skills_to_check:
            matching_skills = [skill for skill in skills_to_check if skill.lower() in st.session_state.resume_text.lower()]
            skill_match_score = (len(matching_skills) / len(skills_to_check)) * 100
            st.subheader("📊 Skill Match Score")
            st.markdown(f"Your skills match {skill_match_score:.1f}% of the requirements for {effective_role}.")
        course_recommendations = {
            "Python": "Python for Everybody - Coursera",
            "Machine Learning": "Machine Learning by Andrew Ng - Coursera",
            "TensorFlow": "TensorFlow Developer Certificate - Coursera",
            "NLP": "Natural Language Processing Specialization - Coursera",
            "HTML": "HTML, CSS, and Javascript for Web Developers - Coursera",
            "CSS": "HTML, CSS, and Javascript for Web Developers - Coursera",
            "JavaScript": "JavaScript: The Complete Guide - Udemy",
            "React": "React - The Complete Guide - Udemy",
            "Node.js": "Node.js, Express, MongoDB & More - Udemy",
            "SQL": "SQL for Data Science - Coursera",
            "REST APIs": "REST API Design, Development & Management - Udemy",
            "Agile": "Agile Project Management - Udemy",
            "Figma": "Figma for UI/UX Design - Udemy",
            "Jira": "Mastering Jira - Udemy",
            "Excel": "Excel Skills for Business - Coursera",
            "Tableau": "Data Visualization with Tableau - Coursera",
            "Networking": "Networking Fundamentals - Cisco Networking Academy",
            "Penetration Testing": "Penetration Testing with Kali Linux - Udemy",
            "Cryptography": "Cryptography I - Coursera",
            "Linux": "Linux Mastery: Master the Linux Command Line - Udemy",
            "Docker": "Docker Mastery: The Complete Guide - Udemy",
            "Kubernetes": "Kubernetes for the Absolute Beginners - Udemy",
            "AWS": "AWS Certified Solutions Architect - Udemy",
            "CI/CD": "CI/CD with Jenkins and GitLab - Coursera",
            "Adobe XD": "Adobe XD for Beginners - Udemy",
            "User Research": "User Research and Design - Coursera",
            "Prototyping": "Prototyping with Figma - Udemy",
            "Scikit-learn": "Machine Learning with Python - Coursera",
            "Deep Learning": "Deep Learning Specialization - Coursera",
            "Solidity": "Solidity and Ethereum Smart Contracts - Udemy",
            "Ethereum": "Blockchain and Ethereum Development - Coursera",
            "Smart Contracts": "Smart Contracts with Solidity - Udemy",
            "Azure": "Microsoft Azure Fundamentals - Coursera",
            "GCP": "Google Cloud Platform Fundamentals - Coursera",
            "Terraform": "Terraform for Beginners - Udemy",
            "R": "R Programming - Coursera",
            "Statistics": "Statistics with R - Coursera",
            "Java": "Java Programming: Complete Beginner to Advanced - Udemy",
            "Git": "Git Complete: The Definitive Guide - Udemy",
            "Algorithms": "Algorithms and Data Structures - Coursera",
            "Swift": "iOS Development with Swift - Udemy",
            "Kotlin": "Kotlin for Android Development - Udemy",
            "React Native": "React Native - The Practical Guide - Udemy",
            "Flutter": "Flutter & Dart - The Complete Guide - Udemy",
            "Problem Solving": "Problem Solving for Developers - Udemy",
            "Communication": "Effective Communication Skills - Coursera"
        }
        if skills_to_check:
            missing_skills = [skill for skill in skills_to_check if skill.lower() in st.session_state.resume_text.lower()]
            if missing_skills:
                st.subheader("🔍 Skill Gap Analysis")
                st.markdown(f"Skills missing for {effective_role}: {', '.join(missing_skills)}")
                st.subheader("📚 Recommended Courses for Skill Gaps")
                for skill in missing_skills:
                    if skill in course_recommendations:
                        st.markdown(f"- {skill}: {course_recommendations[skill]}")
                    else:
                        st.markdown(f"- **{skill}**: No specific course recommendation available. Try searching on Coursera or Udemy.")
            else:
                st.markdown("✅ Your resume covers all key skills for this role!")
        st.subheader("📈 Progress Tracker")
        load_progress()
        roadmap_lines = st.session_state.roadmap.splitlines()
        current_section = None
        section_content = []
        for i, line in enumerate(roadmap_lines):
            line = line.strip()
            if not line:
                continue
            if line.startswith("**"):
                if current_section and section_content:
                    st.markdown(f"## {current_section}")
                    if any(item.startswith("*") for item in section_content):
                        if st.button("Edit Section", key=f"edit_{i-len(section_content)}"):
                            st.session_state.editing_section = i - len(section_content)
                    for content_line in section_content:
                        if content_line.startswith("*"):
                            item_key = f"{current_section}_{content_line}"
                            if item_key not in st.session_state.progress:
                                st.session_state.progress[item_key] = False
                            completed = st.checkbox(f"{content_line[1:]}", value=st.session_state.progress[item_key], key=f"check_{i}_{content_line}")
                            if completed != st.session_state.progress[item_key]:
                                st.session_state.progress[item_key] = completed
                                save_progress()
                        else:
                            st.markdown(content_line)
                current_section = line[2:]
                section_content = []
            else:
                section_content.append(line)
        if current_section and section_content:
            st.markdown(f"## {current_section}")
            if any(item.startswith("*") for item in section_content):
                if st.button("Edit Section", key=f"edit_{len(roadmap_lines)-1}"):
                    st.session_state.editing_section = len(roadmap_lines) - len(section_content)
            for content_line in section_content:
                if content_line.startswith("*"):
                    item_key = f"{current_section}_{content_line}"
                    if item_key not in st.session_state.progress:
                        st.session_state.progress[item_key] = False
                    completed = st.checkbox(f"{content_line[1:]}", value=st.session_state.progress[item_key], key=f"check_{len(roadmap_lines)}_{content_line}")
                    if completed != st.session_state.progress[item_key]:
                        st.session_state.progress[item_key] = completed
                        save_progress()
                else:
                    st.markdown(content_line)
        if st.session_state.editing_section is not None:
            edit_index = st.session_state.editing_section
            section_line = roadmap_lines[edit_index]
            st.subheader(f"Editing Section: {section_line[2:]}")
            new_text = st.text_area("Reword this section:", value=section_line[2:])
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Save Changes"):
                    roadmap_lines[edit_index] = f"**{new_text}"
                    st.session_state.roadmap = "\n".join(roadmap_lines)
                    st.session_state.editing_section = None
                    st.rerun()
            with col2:
                if st.button("Regenerate Section"):
                    if st.session_state.gemini_api_key:
                        with st.spinner("Regenerating section..."):
                            genai.configure(api_key=st.session_state.gemini_api_key)
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            prompt = f"Rewrite this roadmap section for {effective_role}: {section_line[2:]}"
                            response = model.generate_content(prompt)
                            roadmap_lines[edit_index] = f"**{response.text.strip()}"
                            st.session_state.roadmap = "\n".join(roadmap_lines)
                            st.session_state.editing_section = None
                            st.rerun()
                    else:
                        st.error("❌ Please enter a Gemini API key in the sidebar.")
            with col3:
                if st.button("Cancel"):
                    st.session_state.editing_section = None
                    st.rerun()
        st.subheader("❓ Ask About Your Roadmap")
        question = st.text_input("Enter your question (e.g., 'How long will SQL take?')")
        if st.button("Get Answer"):
            if question:
                if not st.session_state.gemini_api_key:
                    st.error("❌ Please enter a Gemini API key in the sidebar.")
                else:
                    try:
                        with st.spinner("Fetching answer..."):
                            genai.configure(api_key=st.session_state.gemini_api_key)
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            response = model.generate_content(f"Roadmap: {st.session_state.roadmap}\nQuestion: {question}")
                            st.markdown(response.text)
                    except Exception as e:
                        st.error(f"❌ Error fetching answer: {e}")
            else:
                st.warning("⚠️ Please enter a question.")
        st.subheader("💬 Was this helpful?")
        col1, col2 = st.columns(2)
        with col1:
            st.button("👍 Yes")
        with col2:
            st.button("👎 No")
        st.subheader("📥 Export Your Roadmap")
        st.download_button(
            label="📄 Download as TXT",
            data=st.session_state.roadmap,
            file_name="SkillWise_Roadmap.txt",
            mime="text/plain"
        )
        # PDF export with fixed formatting
        def clean_text(text):
            # First, handle special characters
            replacements = {
                "–": "-",  # En dash to hyphen
                "—": "-",  # Em dash to hyphen
                "’": "'",  # Right single quote to straight quote
                "‘": "'",  # Left single quote to straight quote
                """: '"',  # Left double quote to straight quote
                """: '"',  # Right double quote to straight quote
                "*": "",  # Remove residual Markdown stars
            }
            for unicode_char, ascii_char in replacements.items():
                text = text.replace(unicode_char, ascii_char)
            
            # Then, handle bullet points and formatting
            text = text.replace(". ", "- ")  # Standardize bullet points
            text = text.replace("•", "-")    # Convert bullet points to hyphens
            text = text.replace("◦", "-")    # Convert sub-bullets to hyphens
            
            # Convert hyphens to colons for better readability
            text = text.replace(" - ", ": ")
            text = text.replace(" -", ": ")
            
            # Clean up any double spaces
            text = " ".join(text.split())
            
            return text.encode("ascii", "ignore").decode("ascii")

        def generate_pdf():
            from io import BytesIO
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Enhanced margins and spacing
            left_margin = 1 * inch
            right_margin = 1 * inch
            top_margin = 1 * inch
            bottom_margin = 0.75 * inch
            content_width = width - left_margin - right_margin

            # Enhanced color scheme
            primary_color = HexColor("#4a69bd")    # Main blue
            accent_color = HexColor("#60a5fa")     # Light blue
            text_color = HexColor("#2d2d44")       # Dark gray
            highlight_color = HexColor("#e0e0e0")  # Light gray
            phase_color = HexColor("#1a1a2e")      # Dark blue for phases

            def draw_header():
                # Draw logo with enhanced positioning
                try:
                    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "logo.png"))
                    logo_width = 1.5 * inch
                    logo_height = 0.5 * inch
                    logo_x = left_margin
                    logo_y = height - 0.7 * inch
                    c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True)
                except Exception as e:
                    # If logo is missing, skip drawing it and print the attempted path
                    print(f"[PDF] Could not load logo at {logo_path}: {e}")
                    try:
                        c.drawImage("logo.png", logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True)
                    except Exception as e2:
                        print(f"[PDF] Fallback logo.png also failed: {e2}")
                    pass
                # Enhanced title styling
                c.setFont("Helvetica-Bold", 24)
                c.setFillColor(primary_color)
                title_x = left_margin + 1.5 * inch + 0.4 * inch
                title_y = height - 0.6 * inch
                c.drawString(title_x, title_y, "SkillWise Learning Roadmap")
                # Decorative line with gradient
                c.setStrokeColor(accent_color)
                c.setLineWidth(2)
                c.line(left_margin, height - 0.8 * inch, width - right_margin, height - 0.8 * inch)

            def draw_footer(page_num):
                # Enhanced footer design
                c.setFont("Helvetica", 8)
                c.setFillColor(text_color)
                footer_text = f"Generated by SkillWise | Page {page_num} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                c.drawCentredString(width / 2, bottom_margin + 0.1 * inch, footer_text)
                
                # Footer decorative line
                c.setStrokeColor(accent_color)
                c.setLineWidth(1)
                c.line(left_margin, bottom_margin + 0.3 * inch, width - right_margin, bottom_margin + 0.3 * inch)

            def draw_section_header(text, y_pos, is_phase=False):
                # Draw section header with enhanced styling
                if is_phase:
                    c.setFont("Helvetica-Bold", 20)
                    c.setFillColor(phase_color)
                    line_spacing = 24
                else:
                    c.setFont("Helvetica-Bold", 16)
                    c.setFillColor(primary_color)
                    line_spacing = 20
                
                # Draw decorative line before header
                c.setStrokeColor(accent_color)
                c.setLineWidth(1)
                c.line(left_margin, y_pos + 0.2 * inch, width - right_margin, y_pos + 0.2 * inch)
                
                # Draw header text
                y_pos = wrap_text(
                    c, text, left_margin, y_pos, content_width,
                    "Helvetica-Bold", 20 if is_phase else 16, line_spacing
                )
                
                # Draw decorative line after header
                c.setStrokeColor(accent_color)
                c.setLineWidth(1)
                c.line(left_margin, y_pos - 0.1 * inch, width - right_margin, y_pos - 0.1 * inch)
                
                return y_pos - 0.2 * inch

            def wrap_text(c, text, x, y, max_width, font_name, font_size, line_spacing=12):
                c.setFont(font_name, font_size)
                words = text.split()
                lines = []
                current_line = []
                current_width = 0

                for word in words:
                    word_width = c.stringWidth(word + " ", font_name, font_size)
                    if current_width + word_width <= max_width:
                        current_line.append(word)
                        current_width += word_width
                    else:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                        current_width = word_width
                if current_line:
                    lines.append(" ".join(current_line))

                for line in lines:
                    c.drawString(x, y, line)
                    y -= line_spacing
                return y

            # Initialize variables
            y_position = height - top_margin
            page_num = 1

            # Draw first page header
            draw_header()
            y_position -= 0.5 * inch

            # Enhanced title section
            c.setFont("Helvetica-Bold", 28)
            c.setFillColor(primary_color)
            y_position = wrap_text(
                c, "Your Personalized Learning Roadmap", left_margin, y_position,
                content_width, "Helvetica-Bold", 28, line_spacing=24
            )
            y_position -= 0.3 * inch

            # Generation date with enhanced styling
            c.setFont("Helvetica", 12)
            c.setFillColor(text_color)
            y_position = wrap_text(
                c, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", left_margin, y_position,
                content_width, "Helvetica", 12, line_spacing=16
            )
            y_position -= 0.4 * inch

            # Process roadmap content with enhanced styling
            lines = st.session_state.roadmap.splitlines()
            current_phase = None
            bullet_indent = left_margin + 0.3 * inch

            for line in lines:
                line = clean_text(line.strip())
                if not line:
                    continue

                if y_position < bottom_margin + 1.5 * inch:
                    draw_footer(page_num)
                    c.showPage()
                    page_num += 1
                    draw_header()
                    y_position = height - top_margin - 0.5 * inch

                if line.startswith("##"):
                    # Phase header
                    text = line[2:].strip()
                    y_position = draw_section_header(text, y_position, is_phase=True)
                    current_phase = text

                elif line.startswith("**") and line.endswith("**"):
                    # Subsection header
                    text = line[2:-2].strip()
                    if y_position < bottom_margin + 2 * inch:
                        draw_footer(page_num)
                        c.showPage()
                        page_num += 1
                        draw_header()
                        y_position = height - top_margin - 0.5 * inch

                    y_position = draw_section_header(text, y_position, is_phase=False)

                elif line.startswith("-"):
                    # Main bullet point
                    text = line[1:].strip()
                    
                    if ":" in text:
                        title, description = text.split(":", 1)
                        title = title.strip()
                        description = description.strip()
                        
                        # Draw bullet point with enhanced styling
                        c.setFont("Helvetica-Bold", 12)
                        c.setFillColor(primary_color)
                        y_position = wrap_text(
                            c, f"• {title}:", bullet_indent, y_position, 
                            content_width - 0.3 * inch, "Helvetica-Bold", 12, line_spacing=16
                        )
                        
                        # Draw description with enhanced styling
                        c.setFont("Helvetica", 11)
                        c.setFillColor(text_color)
                        y_position = wrap_text(
                            c, f"  {description}", bullet_indent + 0.2 * inch, y_position, 
                            content_width - 0.5 * inch, "Helvetica", 11, line_spacing=14
                        )
                    else:
                        # Regular bullet point with enhanced styling
                        c.setFont("Helvetica", 12)
                        c.setFillColor(text_color)
                        y_position = wrap_text(
                            c, f"• {text}", bullet_indent, y_position, 
                            content_width - 0.3 * inch, "Helvetica", 12, line_spacing=16
                        )

                elif line.startswith("  •"):
                    # Sub bullet point
                    text = line[3:].strip()
                    
                    if ":" in text:
                        title, description = text.split(":", 1)
                        title = title.strip()
                        description = description.strip()
                        
                        # Draw sub-bullet point with enhanced styling
                        c.setFont("Helvetica-Bold", 11)
                        c.setFillColor(accent_color)
                        y_position = wrap_text(
                            c, f"  ◦ {title}:", bullet_indent + 0.2 * inch, y_position, 
                            content_width - 0.5 * inch, "Helvetica-Bold", 11, line_spacing=14
                        )
                        
                        # Draw description with enhanced styling
                        c.setFont("Helvetica", 10)
                        c.setFillColor(text_color)
                        y_position = wrap_text(
                            c, f"    {description}", bullet_indent + 0.4 * inch, y_position, 
                            content_width - 0.7 * inch, "Helvetica", 10, line_spacing=12
                        )
                    else:
                        # Regular sub-bullet point with enhanced styling
                        c.setFont("Helvetica", 11)
                        c.setFillColor(text_color)
                        y_position = wrap_text(
                            c, f"  ◦ {text}", bullet_indent + 0.2 * inch, y_position, 
                            content_width - 0.5 * inch, "Helvetica", 11, line_spacing=14
                        )

                else:
                    # Regular text with enhanced styling
                    c.setFont("Helvetica", 11)
                    c.setFillColor(text_color)
                    y_position = wrap_text(
                        c, line, left_margin, y_position, content_width,
                        "Helvetica", 11, line_spacing=14
                    )

            draw_footer(page_num)
            c.save()
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes

        if st.button("📄 Download as PDF"):
            try:
                pdf_bytes = generate_pdf()
                st.download_button(
                    label="📄 Click to Download PDF",
                    data=pdf_bytes,
                    file_name="SkillWise_Roadmap.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
        
        roadmap_data = {
            "resume": st.session_state.resume_text,
            "goal": st.session_state.goal,
            "role": effective_role,
            "roadmap": st.session_state.roadmap,
            "timestamp": datetime.now().isoformat()
        }
        st.download_button(
            label="💾 Download as JSON",
            data=json.dumps(roadmap_data, indent=2),
            file_name="SkillWise_Roadmap.json",
            mime="application/json"
        )
        
        unique_id = hash(st.session_state.roadmap) % 1000000
        with open(f"roadmap_{unique_id}.json", "w") as f:
            json.dump(roadmap_data, f)
        st.markdown(f"🔗 Shareable link: `http://skillwise.local/roadmap/{unique_id}` (Note: Deploy to a server for real links)")
    else:
        st.info("🚧 Generate a roadmap in the Resume tab.")

# Footer
st.markdown("""
<div class="footer">
    <div class="social-icons">
        <a href="https://github.com/Sahaj33-op/" target="_blank"><i class="fab fa-github"></i></a>
    </div>
    <p>© 2025 SkillWise. All rights reserved.</p>
    <p>
        <a href="https://linktr.ee/sahaj33">Contact Me</a>
    </p>
</div>
""", unsafe_allow_html=True)
