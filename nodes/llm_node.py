"""
LLM Node for NFL Player Performance Chatbot.

This module implements the LLM Node that generates natural language insights
from retrieved player statistics using OpenAI's language models.

Requirements addressed:
- 5.1: Provide context such as league averages, rankings, or historical comparisons
- 5.2: Identify and highlight notable trends in player performance data
- 5.3: Include situational statistics when relevant
- 5.4: Generate insights that explain why certain statistics are significant
- 5.5: Cite specific data points when making claims
- 2.3: Highlight significant differences with percentage changes or absolute values
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from models.models import ChatbotState
from error_handler import ChatbotError, ErrorType, log_error

logger = logging.getLogger(__name__)


def format_dataframe_for_prompt(df: pd.DataFrame) -> str:
    """
    Format DataFrame into a readable string for LLM prompt.
    
    Args:
        df: DataFrame with player statistics
        
    Returns:
        Formatted string representation of the data
    """
    if df.empty:
        return "No data available."
    
    # Convert DataFrame to a structured format
    formatted_lines = []
    
    for idx, row in df.iterrows():
        player_info = []
        
        # Basic info
        if 'player_name' in row:
            player_info.append(f"Player: {row['player_name']}")
        if 'team' in row:
            player_info.append(f"Team: {row['team']}")
        if 'position' in row:
            player_info.append(f"Position: {row['position']}")
        if 'season' in row:
            player_info.append(f"Season: {int(row['season'])}")
        if 'week' in row and pd.notna(row['week']):
            player_info.append(f"Week: {int(row['week'])}")
        
        formatted_lines.append(" | ".join(player_info))
        
        # Statistics
        stat_lines = []
        stat_columns = [col for col in df.columns if col not in 
                       ['player_name', 'team', 'position', 'season', 'week', 'games_played']]
        
        for col in stat_columns:
            if pd.notna(row[col]) and row[col] != 0:
                # Format the stat name nicely
                stat_name = col.replace('_', ' ').title()
                value = row[col]
                
                # Format based on type
                if isinstance(value, float):
                    if 'rate' in col or 'percentage' in col:
                        stat_lines.append(f"  {stat_name}: {value:.1f}%")
                    else:
                        stat_lines.append(f"  {stat_name}: {value:.2f}")
                else:
                    stat_lines.append(f"  {stat_name}: {value}")
        
        if stat_lines:
            formatted_lines.extend(stat_lines)
        
        formatted_lines.append("")  # Empty line between players
    
    return "\n".join(formatted_lines)


def calculate_comparison_metrics(df: pd.DataFrame) -> Dict[str, any]:
    """
    Calculate comparison metrics between players.
    
    Args:
        df: DataFrame with multiple players' statistics
        
    Returns:
        Dictionary with comparison insights
    """
    if df.empty or len(df) < 2:
        return {}
    
    metrics = {
        'player_count': len(df),
        'comparisons': []
    }
    
    # Get numeric columns for comparison
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    stat_cols = [col for col in numeric_cols if col not in ['season', 'week', 'games_played']]
    
    # Calculate differences for each stat
    for stat in stat_cols:
        if stat in df.columns and df[stat].notna().any():
            values = df[stat].dropna()
            if len(values) >= 2:
                max_val = values.max()
                min_val = values.min()
                
                if max_val > 0:
                    pct_diff = ((max_val - min_val) / max_val) * 100
                    
                    # Find players with max and min values
                    max_player = df.loc[df[stat] == max_val, 'player_name'].iloc[0] if 'player_name' in df.columns else 'Unknown'
                    min_player = df.loc[df[stat] == min_val, 'player_name'].iloc[0] if 'player_name' in df.columns else 'Unknown'
                    
                    metrics['comparisons'].append({
                        'stat': stat,
                        'max_value': max_val,
                        'min_value': min_val,
                        'difference': max_val - min_val,
                        'percent_difference': pct_diff,
                        'leader': max_player,
                        'trailing': min_player
                    })
    
    return metrics


def calculate_league_context(df: pd.DataFrame, stat: str) -> Dict[str, any]:
    """
    Calculate league context for a statistic (averages, rankings).
    
    Note: This is a simplified version. In production, you would query
    actual league-wide data for accurate context.
    
    Args:
        df: DataFrame with player statistics
        stat: Statistic to provide context for
        
    Returns:
        Dictionary with league context information
    """
    context = {}
    
    if stat not in df.columns or df[stat].isna().all():
        return context
    
    # Calculate basic statistics
    values = df[stat].dropna()
    if len(values) > 0:
        context['mean'] = values.mean()
        context['median'] = values.median()
        context['std'] = values.std()
        context['min'] = values.min()
        context['max'] = values.max()
    
    # Approximate league averages (these would come from actual data in production)
    # These are rough 2023 NFL averages for common stats
    league_averages = {
        'passing_yards': 250,
        'passing_touchdowns': 1.5,
        'completion_rate': 64.0,
        'interceptions': 0.8,
        'rushing_yards': 80,
        'rushing_touchdowns': 0.5,
        'receiving_yards': 50,
        'receptions': 4.5,
        'targets': 6.5,
        'yards_per_attempt': 7.0,
        'yards_per_reception': 11.0,
    }
    
    if stat in league_averages:
        context['league_average'] = league_averages[stat]
    
    return context


def format_conversation_history(conversation_history: List[Dict]) -> str:
    """
    Format conversation history for inclusion in prompt.
    
    Args:
        conversation_history: List of previous conversation turns
        
    Returns:
        Formatted string of recent conversation
    """
    if not conversation_history:
        return "No previous conversation."
    
    # Get last 5 turns for better context on follow-up questions
    recent_turns = conversation_history[-5:] if len(conversation_history) >= 5 else conversation_history
    
    formatted = []
    for i, turn in enumerate(recent_turns, 1):
        user_query = turn.get('user_query', '')
        bot_response = turn.get('bot_response', '')
        mentioned_players = turn.get('mentioned_players', [])
        mentioned_stats = turn.get('mentioned_stats', [])
        
        if user_query:
            formatted.append(f"Turn {i} - User: {user_query}")
        if bot_response:
            # Truncate long responses but keep key info
            if len(bot_response) > 300:
                bot_response = bot_response[:300] + "..."
            formatted.append(f"Turn {i} - Assistant: {bot_response}")
        
        # Add context about what was discussed
        if mentioned_players or mentioned_stats:
            context_parts = []
            if mentioned_players:
                context_parts.append(f"Players: {', '.join(mentioned_players)}")
            if mentioned_stats:
                context_parts.append(f"Stats: {', '.join(mentioned_stats)}")
            formatted.append(f"  [Context: {' | '.join(context_parts)}]")
        
        formatted.append("")
    
    return "\n".join(formatted)


def build_insight_prompt(
    retrieved_data: pd.DataFrame,
    parsed_query: Dict,
    conversation_history: List[Dict]
) -> str:
    """
    Build the system prompt for generating insights.
    
    Args:
        retrieved_data: DataFrame with player statistics
        parsed_query: Parsed query structure
        conversation_history: Previous conversation turns
        
    Returns:
        Formatted prompt string
    """
    current_year = datetime.now().year
    
    # Format the data
    data_str = format_dataframe_for_prompt(retrieved_data)
    
    # Calculate comparison metrics if applicable
    comparison_metrics = {}
    if parsed_query.get('comparison') and len(retrieved_data) > 1:
        comparison_metrics = calculate_comparison_metrics(retrieved_data)
    
    # Build the prompt
    prompt = f"""You are an expert NFL analyst providing insights about player statistics. Your goal is to generate clear, informative, and contextual analysis based on the data provided.

CURRENT CONTEXT:
- Current Year: {current_year}
- Query Type: {parsed_query.get('query_intent', 'player_stats')}
- Comparison Query: {'Yes' if parsed_query.get('comparison') else 'No'}

PLAYER STATISTICS:
{data_str}
"""

    # Add comparison metrics if available
    if comparison_metrics and comparison_metrics.get('comparisons'):
        prompt += "\n\nCOMPARISON INSIGHTS:\n"
        for comp in comparison_metrics['comparisons'][:5]:  # Top 5 differences
            stat_name = comp['stat'].replace('_', ' ').title()
            prompt += f"- {stat_name}: {comp['leader']} leads with {comp['max_value']:.1f} vs {comp['trailing']} with {comp['min_value']:.1f} "
            prompt += f"(difference: {comp['difference']:.1f}, {comp['percent_difference']:.1f}% gap)\n"
    
    # Add conversation context
    if conversation_history:
        history_str = format_conversation_history(conversation_history)
        prompt += f"\n\nRECENT CONVERSATION HISTORY:\n{history_str}\n"
        prompt += "\n**IMPORTANT**: This is a follow-up question. Use the conversation history above to:\n"
        prompt += "- Understand references like 'he', 'his', 'that player', 'them', etc.\n"
        prompt += "- Maintain continuity with previous answers\n"
        prompt += "- Build upon previously discussed topics\n"
        prompt += "- Reference earlier statistics when relevant\n\n"
    
    prompt += """

INSTRUCTIONS FOR GENERATING INSIGHTS:

1. **Maintain Conversation Context**: If there's conversation history, this is a follow-up question. Reference previous topics naturally and resolve pronouns using the history.
2. **Cite Specific Data**: Always reference actual numbers from the statistics provided
3. **Provide Context**: Compare to league averages, historical performance, or other relevant benchmarks when possible
4. **Highlight Trends**: Identify notable patterns, improvements, or declines in performance
5. **Explain Significance**: Don't just state numbers - explain what they mean and why they matter
6. **Use Comparisons**: When comparing players, use percentage differences and absolute values
7. **Be Conversational**: Write in a natural, engaging tone while maintaining accuracy
8. **Structure Clearly**: Use bullet points or short paragraphs for readability

FORMATTING GUIDELINES:
- Use percentage changes when comparing (e.g., "15% more yards")
- Include absolute differences (e.g., "300 more yards")
- Highlight exceptional performance (top 10%, career highs, etc.)
- Mention relevant situational context (playoff performance, division games, etc.)
- Keep responses concise but informative (3-5 paragraphs or equivalent bullet points)

LEAGUE CONTEXT (Approximate 2023 NFL Averages per game):
- Passing Yards: ~250 yards
- Passing TDs: ~1.5 per game
- Completion Rate: ~64%
- Rushing Yards: ~80 yards per game
- Receiving Yards: ~50 yards per game
- Receptions: ~4.5 per game

Generate a comprehensive yet concise analysis based on the data and context provided above.
"""
    
    return prompt


async def generate_insights(state: ChatbotState) -> ChatbotState:
    """
    Generate natural language insights from retrieved player statistics.
    
    This is the main entry point for the LLM Node in the LangGraph workflow.
    
    Args:
        state: Current chatbot state with retrieved_data
        
    Returns:
        Updated state with generated_response field populated
        
    Requirements:
        - 5.1: Provides context like league averages and rankings
        - 5.2: Identifies and highlights notable trends
        - 5.3: Includes situational statistics when relevant
        - 5.4: Explains why statistics are significant
        - 5.5: Cites specific data points
        - 2.3: Highlights differences with percentage changes
    """
    try:
        # Check for errors from previous nodes
        if state.get("error") and state.get("error") != "":
            # Error already handled, skip LLM generation
            return state
        
        retrieved_data = state.get("retrieved_data")
        parsed_query = state.get("parsed_query", {})
        conversation_history = state.get("conversation_history", [])
        
        # Validate retrieved data
        if retrieved_data is None or retrieved_data.empty:
            raise ChatbotError(
                error_type=ErrorType.NO_DATA_FOUND,
                message="No data available for insight generation",
                details={"parsed_query": parsed_query},
                recoverable=True
            )
        
        # Build the prompt
        system_prompt = build_insight_prompt(
            retrieved_data=retrieved_data,
            parsed_query=parsed_query,
            conversation_history=conversation_history
        )
        
        # Initialize OpenAI
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,  # Some creativity for engaging insights
            max_tokens=800,  # Limit response length
        )
        
        # Create messages
        user_query = state.get("user_query", "Analyze these statistics")
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User's question: {user_query}")
        ]
        
        # Generate insights
        logger.info("Generating insights from LLM...")
        response = llm.invoke(messages)
        
        # Extract the generated text
        generated_response = response.content
        
        # Store in state
        state["generated_response"] = generated_response
        
        logger.info(f"Successfully generated insights ({len(generated_response)} characters)")
        
        return state
        
    except ChatbotError:
        # Re-raise ChatbotError to be handled by workflow
        raise
    except Exception as e:
        # Handle LLM API errors
        log_error(
            e,
            context={
                "operation": "insight_generation",
                "data_size": len(retrieved_data) if retrieved_data is not None else 0
            },
            level="warning"
        )
        
        # Determine specific error type
        error_str = str(e).lower()
        if "rate" in error_str and "limit" in error_str:
            error_type = ErrorType.LLM_RATE_LIMIT
        elif "timeout" in error_str:
            error_type = ErrorType.LLM_TIMEOUT
        else:
            error_type = ErrorType.INSIGHT_GENERATION_ERROR
        
        raise ChatbotError(
            error_type=error_type,
            message=f"Failed to generate insights: {str(e)}",
            details={"error": str(e)},
            recoverable=True
        )


# Synchronous version for non-async contexts
def generate_insights_sync(state: ChatbotState) -> ChatbotState:
    """
    Synchronous version of generate_insights for compatibility.
    
    Args:
        state: Current chatbot state
        
    Returns:
        Updated state with generated insights
    """
    import asyncio
    
    # Run async function in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(generate_insights(state))
