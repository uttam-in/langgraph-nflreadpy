"""
Generate LangGraph workflow diagram.

This script creates a visual representation of the NFL Player Performance
Chatbot workflow using LangGraph's built-in visualization capabilities.
"""

import logging
from workflow import create_workflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_diagram(output_path: str = "workflow_diagram.png"):
    """
    Generate and save the workflow diagram.
    
    Args:
        output_path: Path where the diagram image will be saved
    """
    try:
        # Create the workflow
        logger.info("Creating workflow...")
        workflow = create_workflow()
        
        # Compile the workflow
        logger.info("Compiling workflow...")
        compiled_workflow = workflow.compile()
        
        # Generate the diagram
        logger.info(f"Generating diagram to {output_path}...")
        
        # Get the Mermaid diagram representation
        try:
            # Try to get PNG image
            png_data = compiled_workflow.get_graph().draw_mermaid_png()
            
            with open(output_path, "wb") as f:
                f.write(png_data)
            
            logger.info(f"✓ Diagram saved successfully to {output_path}")
            
        except Exception as e:
            # Fallback to Mermaid text format
            logger.warning(f"Could not generate PNG: {e}")
            logger.info("Generating Mermaid text format instead...")
            
            mermaid_text = compiled_workflow.get_graph().draw_mermaid()
            
            text_output_path = output_path.replace(".png", ".mmd")
            with open(text_output_path, "w") as f:
                f.write(mermaid_text)
            
            logger.info(f"✓ Mermaid diagram saved to {text_output_path}")
            logger.info("You can visualize this at: https://mermaid.live/")
            
            # Also print to console
            print("\n" + "="*80)
            print("MERMAID DIAGRAM")
            print("="*80)
            print(mermaid_text)
            print("="*80)
            print(f"\nCopy the above text to https://mermaid.live/ to visualize")
            print("="*80 + "\n")
            
    except Exception as e:
        logger.error(f"Error generating diagram: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    generate_diagram()
