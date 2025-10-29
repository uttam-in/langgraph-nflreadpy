"""Generate Mermaid text diagram of the workflow."""

from workflow import create_workflow

# Create and compile workflow
workflow = create_workflow()
compiled_workflow = workflow.compile()

# Get Mermaid diagram
mermaid_text = compiled_workflow.get_graph().draw_mermaid()

# Save to file
with open("workflow_diagram.mmd", "w") as f:
    f.write(mermaid_text)

# Print to console
print(mermaid_text)
