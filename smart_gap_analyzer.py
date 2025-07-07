import google.generativeai as genai
import streamlit as st # For accessing API key from session state

class SmartGapAnalysisError(Exception):
    """Custom exception for smart gap analysis errors."""
    pass

def get_smart_gap_analysis(resume_text: str, target_role: str, user_goal: str = "") -> str:
    """
    Performs a smart gap analysis using an LLM.

    Args:
        resume_text (str): The text of the user's resume.
        target_role (str): The target job role (e.g., "AI Engineer").
        user_goal (str): The user's stated career goal (optional, for more context).

    Returns:
        str: A narrative gap analysis.

    Raises:
        SmartGapAnalysisError: If the analysis fails.
    """
    if not st.session_state.get("gemini_api_key"):
        raise SmartGapAnalysisError("Gemini API key not configured in session state.")

    genai.configure(api_key=st.session_state.gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash") # Or your preferred model

    # Step 1: Define what an ideal candidate for the target_role looks like (implicitly or explicitly)
    # For this implementation, we'll use a single, more complex prompt.

    prompt_parts = [
        "Analyze the provided resume against the typical requirements and expectations for a professional in the role of an '{}'.".format(target_role),
        "The user's career goal is: '{}' (if provided, otherwise focus on the target role).".format(user_goal) if user_goal else "",
        "\nResume Text:\n---\n{}\n---".format(resume_text),
        "\nPlease provide a concise, insightful gap analysis. Focus on:",
        "1. Key skills or technologies the resume demonstrates for this role.",
        "2. Specific skills, experiences (e.g., types of projects, methodologies), or qualifications that appear to be missing or underdeveloped for an ideal '{}' candidate.".format(target_role),
        "3. Suggest 1-2 actionable areas for improvement or focus.",
        "4. Present this as a narrative, not just a list. For example: 'While your resume shows good foundational knowledge in X, a typical {} role would also expect more demonstrated experience with Y, such as hands-on projects using Z.'".format(target_role),
        "Avoid generic advice. Be specific to the resume content and the role."
    ]

    prompt = "\n".join(filter(None, prompt_parts))

    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        else:
            raise SmartGapAnalysisError("Received an empty response from the LLM.")
    except Exception as e:
        # Log the actual error for debugging if necessary
        # print(f"LLM generation error: {e}")
        raise SmartGapAnalysisError(f"Failed to generate smart gap analysis due to an LLM error: {str(e)}")

if __name__ == '__main__':
    # This is for testing the module directly if needed.
    # You'd need to set up st.session_state.gemini_api_key or mock it.
    # Example:
    # st.session_state.gemini_api_key = "YOUR_API_KEY"
    print("Testing smart_gap_analyzer (requires API key and Streamlit context or mocking)")

    # Mock resume and role for a quick test
    mock_resume = """
    John Doe
    Software Engineer

    Education:
    B.S. Computer Science

    Skills:
    Python, Java, SQL

    Experience:
    Intern at Tech Corp - Developed web components.
    """
    mock_role = "Senior Python Developer"
    mock_goal = "To become a lead developer specializing in backend systems."

    # try:
    #     # This direct call won't work without Streamlit running or st.session_state being populated.
    #     # analysis = get_smart_gap_analysis(mock_resume, mock_role, mock_goal)
    #     # print("\nAnalysis Result:\n", analysis)
    #     print("To test, run within a Streamlit app context or mock st.session_state.")
    # except SmartGapAnalysisError as e:
    #     print(f"Error: {e}")
    # except Exception as e:
    #     print(f"An unexpected error occurred: {e}")
    pass
