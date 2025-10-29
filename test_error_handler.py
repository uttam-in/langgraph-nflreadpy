"""
Test script for error handler module.
"""

from error_handler import (
    ErrorType,
    ChatbotError,
    get_user_friendly_message,
    handle_error,
    create_error_response
)

def test_error_messages():
    """Test user-friendly error messages."""
    print("\n" + "=" * 80)
    print("Testing User-Friendly Error Messages")
    print("=" * 80)
    
    # Test a few error types
    error_types = [
        ErrorType.NO_DATA_FOUND,
        ErrorType.PLAYER_NOT_FOUND,
        ErrorType.DATA_SOURCE_UNAVAILABLE,
        ErrorType.QUERY_PARSING_ERROR
    ]
    
    for error_type in error_types:
        msg = get_user_friendly_message(error_type, include_suggestions=False)
        print(f"\n{error_type.value}:")
        print(f"  {msg}")


def test_chatbot_error():
    """Test ChatbotError exception."""
    print("\n" + "=" * 80)
    print("Testing ChatbotError Exception")
    print("=" * 80)
    
    try:
        raise ChatbotError(
            error_type=ErrorType.PLAYER_NOT_FOUND,
            message="Player 'Test Player' not found",
            details={"player": "Test Player", "season": 2023},
            recoverable=True
        )
    except ChatbotError as e:
        print(f"\nError Type: {e.error_type.value}")
        print(f"Message: {e.message}")
        print(f"Recoverable: {e.recoverable}")
        print(f"Details: {e.details}")


def test_handle_error():
    """Test error handling function."""
    print("\n" + "=" * 80)
    print("Testing handle_error Function")
    print("=" * 80)
    
    try:
        raise ValueError("Test error for demonstration")
    except Exception as e:
        error_info = handle_error(
            e,
            context={"test": "context", "operation": "test_operation"},
            default_error_type=ErrorType.UNKNOWN_ERROR
        )
        print(f"\nError Type: {error_info['error_type']}")
        print(f"Recoverable: {error_info['recoverable']}")
        print(f"User Message (first 150 chars):")
        print(f"  {error_info['user_message'][:150]}...")


def test_error_response():
    """Test error response creation."""
    print("\n" + "=" * 80)
    print("Testing create_error_response Function")
    print("=" * 80)
    
    response = create_error_response(
        ErrorType.DATA_RETRIEVAL_FAILED,
        custom_message="Failed to retrieve data for Patrick Mahomes",
        details={"player": "Patrick Mahomes", "season": 2023}
    )
    
    print(f"\nError: {response['error']}")
    print(f"Generated Response (first 150 chars):")
    print(f"  {response['generated_response'][:150]}...")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ERROR HANDLER MODULE TESTS")
    print("=" * 80)
    
    test_error_messages()
    test_chatbot_error()
    test_handle_error()
    test_error_response()
    
    print("\n" + "=" * 80)
    print("All tests completed successfully!")
    print("=" * 80 + "\n")
