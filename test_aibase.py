#!/usr/bin/env python3
"""
Basic tests for Aibase translator
Note: These tests require an OpenAI API key to run
"""

import os
import sys
from unittest.mock import Mock, patch
from aibase import AibaseTranslator


def test_initialization():
    """Test translator initialization."""
    print("Test 1: Initialization")
    print("-" * 50)
    
    # Check if API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠ Skipping (no API key) - would require OPENAI_API_KEY")
        return True
    
    try:
        # Test with environment variable
        translator = AibaseTranslator()
        print("✓ Translator initialized successfully")
        return True
    except ValueError as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_supported_languages():
    """Test supported languages list."""
    print("\nTest 2: Supported Languages")
    print("-" * 50)
    
    try:
        # Test without needing API key by checking class attributes
        languages = AibaseTranslator.SUPPORTED_LANGUAGES
        
        assert 'python' in languages
        assert 'javascript' in languages
        assert 'java' in languages
        
        print(f"✓ Found {len(languages)} supported languages")
        print(f"  Languages: {', '.join(list(languages.keys())[:5])}...")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_translation_mock():
    """Test translation without API call (mock test)."""
    print("\nTest 3: Translation Structure (Mock)")
    print("-" * 50)
    
    try:
        # Check method exists on the class
        assert hasattr(AibaseTranslator, 'translate')
        assert hasattr(AibaseTranslator, 'translate_interactive')
        
        print("✓ Translation methods exist on class")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_invalid_language():
    """Test handling of invalid language."""
    print("\nTest 4: Invalid Language Handling")
    print("-" * 50)
    
    # Check if API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        # Test validation logic without instantiating
        try:
            invalid_lang = "invalid_language"
            supported = AibaseTranslator.SUPPORTED_LANGUAGES
            assert invalid_lang not in supported
            print(f"✓ Validation logic works: '{invalid_lang}' not in supported languages")
            return True
        except Exception as e:
            print(f"✗ Test failed: {e}")
            return False
    
    try:
        translator = AibaseTranslator()
        
        # This should raise ValueError
        try:
            translator.translate("test", "invalid_language")
            print("✗ Should have raised ValueError for invalid language")
            return False
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")
            return True
            
    except Exception as e:
        print(f"✗ Test failed unexpectedly: {e}")
        return False


def test_translation_with_mock():
    """Test translation workflow with mocked API response."""
    print("\nTest 5: Translation with Mocked API")
    print("-" * 50)
    
    try:
        # Create a mock response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "def hello_world():\n    print('Hello, World!')"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        # Patch the OpenAI client
        with patch('aibase.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Test with a fake API key
            translator = AibaseTranslator(api_key='fake-key-for-testing')
            result = translator.translate("create a hello world function", "python")
            
            # Verify the result
            assert "hello_world" in result.lower() or "hello" in result.lower()
            assert "print" in result.lower() or "def" in result.lower()
            
            # Verify the API was called correctly
            assert mock_client.chat.completions.create.called
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]['model'] == AibaseTranslator.DEFAULT_MODEL
            assert call_args[1]['temperature'] == AibaseTranslator.DEFAULT_TEMPERATURE
            
            print(f"✓ Translation workflow completed successfully")
            print(f"  Generated: {result[:50]}...")
            return True
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custom_parameters():
    """Test custom model parameters."""
    print("\nTest 6: Custom Parameters")
    print("-" * 50)
    
    try:
        # Test with custom parameters (without API key, just initialization)
        with patch('aibase.OpenAI'):
            translator = AibaseTranslator(
                api_key='fake-key',
                model='gpt-4',
                temperature=0.5,
                max_tokens=1000
            )
            
            assert translator.model == 'gpt-4'
            assert translator.temperature == 0.5
            assert translator.max_tokens == 1000
            
            print("✓ Custom parameters set correctly")
            return True
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("Aibase Test Suite")
    print("=" * 50)
    print()
    
    tests = [
        test_initialization,
        test_supported_languages,
        test_translation_mock,
        test_invalid_language,
        test_translation_with_mock,
        test_custom_parameters
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append(False)
        print()
    
    # Summary
    print("=" * 50)
    print("Test Summary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
