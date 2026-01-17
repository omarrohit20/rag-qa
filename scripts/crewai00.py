

# Warning control
import warnings
import sys
from pathlib import Path

warnings.filterwarnings('ignore')

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_cohere import ChatCohere
from langchain_core.messages import HumanMessage, SystemMessage
from src.config import COHERE_API_KEY, COHERE_MODEL

# Initialize Cohere language model (LLM)
llm = ChatCohere(
    model=COHERE_MODEL,
    temperature=0.7,
    cohere_api_key=COHERE_API_KEY
)

# Define agent roles and prompts
class Agent:
    def __init__(self, role, goal, backstory, llm):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.llm = llm
    
    def execute(self, task_description, context=""):
        """Execute the agent task using the LLM"""
        system_prompt = f"""You are a {self.role}.
Goal: {self.goal}
Backstory: {self.backstory}

Provide clear, well-structured output for your assigned task."""
        
        user_prompt = f"{task_description}\n\nContext: {context}" if context else task_description
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content

# Create agents with Cohere LLM
planner = Agent(
    role="Content Planner",
    goal="Plan engaging and factually accurate content",
    backstory="You're working on planning a blog article. "
              "You collect information that helps the audience learn something "
              "and make informed decisions. Your work is the basis for the Content Writer.",
    llm=llm
)

writer = Agent(
    role="Content Writer",
    goal="Write insightful and factually accurate opinion pieces",
    backstory="You're working on writing a new opinion piece. "
              "You base your writing on the Content Planner's outline and context. "
              "You follow the main objectives and provide objective, impartial insights.",
    llm=llm
)

editor = Agent(
    role="Editor",
    goal="Edit blog posts to align with organizational writing style",
    backstory="You review blog posts to ensure they follow journalistic best practices, "
              "provide balanced viewpoints, and avoid controversial topics.",
    llm=llm
)

# Define tasks
class Task:
    def __init__(self, description, expected_output, agent):
        self.description = description
        self.expected_output = expected_output
        self.agent = agent

plan_task = Task(
    description=(
        "Create a content plan that includes:\n"
        "1. Prioritize the latest trends, key players, and noteworthy news\n"
        "2. Identify the target audience and their interests\n"
        "3. Develop a detailed content outline with introduction, key points, and call to action\n"
        "4. Include SEO keywords and relevant data sources"
    ),
    expected_output="A comprehensive content plan with outline, audience analysis, SEO keywords, and resources",
    agent=planner
)

write_task = Task(
    description=(
        "Using the content plan, write a compelling blog post that:\n"
        "1. Uses the content plan to craft the post\n"
        "2. Incorporates SEO keywords naturally\n"
        "3. Has properly named sections/subtitles in an engaging manner\n"
        "4. Is structured with introduction, body, and conclusion\n"
        "5. Is proofread for grammatical errors"
    ),
    expected_output="A well-written blog post in markdown format, ready for publication",
    agent=writer
)

edit_task = Task(
    description="Proofread and edit the blog post for grammatical errors, style consistency, and brand alignment",
    expected_output="A polished, publication-ready blog post in markdown format",
    agent=editor
)

# Execute workflow
def run_content_workflow(topic="Artificial Intelligence"):
    """Run the multi-agent content creation workflow"""
    print("="*70)
    print(f"🚀 STARTING CONTENT WORKFLOW: {topic}")
    print("="*70)
    
    # Step 1: Planning
    print("\n📋 STEP 1: CONTENT PLANNING")
    print("-" * 70)
    plan_output = planner.execute(
        f"{plan_task.description}\n\nTopic: {topic}"
    )
    print(plan_output[:500] + "...\n")
    
    # Step 2: Writing
    print("\n✍️  STEP 2: CONTENT WRITING")
    print("-" * 70)
    write_output = writer.execute(
        f"{write_task.description}\n\nTopic: {topic}",
        context=f"Content Plan:\n{plan_output}"
    )
    print(write_output[:500] + "...\n")
    
    # Step 3: Editing
    print("\n✏️  STEP 3: EDITING & REVIEW")
    print("-" * 70)
    final_output = editor.execute(
        f"{edit_task.description}",
        context=f"Draft Blog Post:\n{write_output}"
    )
    
    # Print final result
    print("\n" + "="*70)
    print("✅ FINAL PUBLISHED CONTENT")
    print("="*70)
    print(final_output)
    print("="*70)
    
    return {
        "topic": topic,
        "plan": plan_output,
        "draft": write_output,
        "final": final_output
    }

# Run the workflow
if __name__ == "__main__":
    result = run_content_workflow("Artificial Intelligence")