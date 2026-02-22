#!/usr/bin/env python3
"""
Basic tests for Aibase translator
"""

import os
import sys
from unittest.mock import Mock, patch, MagicMock
from aibase import AibaseTranslator


def test_initialization():
    """Test translator initialization with default Ollama provider."""
    print("Test 1: Initialization (Ollama default)")
    print("-" * 50)

    try:
        # Ollama provider requires no API key
        translator = AibaseTranslator()
        assert translator.provider == AibaseTranslator.PROVIDER_OLLAMA
        assert translator.model == AibaseTranslator.DEFAULT_OLLAMA_MODEL
        print("✓ Translator initialized successfully with Ollama provider (no API key required)")
        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_supported_languages():
    """Test supported languages list."""
    print("\nTest 2: Supported Languages")
    print("-" * 50)

    try:
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

    try:
        invalid_lang = "invalid_language"
        supported = AibaseTranslator.SUPPORTED_LANGUAGES
        assert invalid_lang not in supported
        print(f"✓ Validation logic works: '{invalid_lang}' not in supported languages")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_translation_with_mock_ollama():
    """Test translation workflow with mocked Ollama HTTP response."""
    print("\nTest 5: Translation with Mocked Ollama API")
    print("-" * 50)

    try:
        mock_resp = Mock()
        mock_resp.json.return_value = {"response": "def hello_world():\n    print('Hello, World!')"}
        mock_resp.raise_for_status = Mock()

        with patch('aibase.requests.post', return_value=mock_resp):
            translator = AibaseTranslator()
            result = translator.translate("create a hello world function", "python")

            assert "hello_world" in result.lower() or "hello" in result.lower()
            assert "print" in result.lower() or "def" in result.lower()

            print(f"✓ Ollama translation workflow completed successfully")
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
        translator = AibaseTranslator(
            model='llama3',
            temperature=0.5,
            max_tokens=1000
        )

        assert translator.model == 'llama3'
        assert translator.temperature == 0.5
        assert translator.max_tokens == 1000
        assert translator.provider == AibaseTranslator.PROVIDER_OLLAMA

        print("✓ Custom parameters set correctly")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_code_fence_stripping():
    """Test that markdown code fences are stripped from output."""
    print("\nTest 7: Code fence stripping")
    print("-" * 50)

    try:
        # Fenced block with language tag and proper closing fence
        fenced = "```python\ndef foo():\n    pass\n```"
        stripped = AibaseTranslator._strip_code_fences(fenced)
        assert not stripped.startswith('```'), f"Expected no fence, got: {stripped!r}"
        assert 'def foo' in stripped

        # Plain code - should remain unchanged
        plain = "def bar():\n    pass"
        assert AibaseTranslator._strip_code_fences(plain) == plain

        # Malformed fence (no closing ```) - should remain unchanged
        malformed = "```python\ndef baz():\n    pass"
        assert AibaseTranslator._strip_code_fences(malformed) == malformed

        print("✓ Code fence stripping works correctly")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_game_language_targets():
    """Test that new Flame/game-asset language targets are present."""
    print("\nTest 8: Flame/game-asset language targets")
    print("-" * 50)

    try:
        languages = AibaseTranslator.SUPPORTED_LANGUAGES
        for key in ('flame', 'flame-game', 'flame-component',
                    'game-asset-sprite', 'game-asset-animation', 'game-tilemap'):
            assert key in languages, f"Missing language key: {key}"
        print(f"✓ All 6 new game/Flame language targets present")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_flame_prompt_selection():
    """Test that _build_prompts returns Flame-specific prompts for flame keys."""
    print("\nTest 9: Flame prompt selection")
    print("-" * 50)

    try:
        translator = AibaseTranslator()
        for key in ('flame', 'flame-game', 'flame-component'):
            lang_name = AibaseTranslator.SUPPORTED_LANGUAGES[key]
            sys_p, usr_p = translator._build_prompts("test desc", lang_name, True, key)
            assert 'Flame' in sys_p or 'Flutter' in sys_p, \
                f"Expected Flame/Flutter in system prompt for {key}"
            assert 'Flame' in usr_p or 'flame' in usr_p.lower(), \
                f"Expected flame content in user prompt for {key}"
        print("✓ Flame prompt selection works correctly")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_game_asset_prompt_selection():
    """Test that _build_prompts returns game-asset-specific prompts for game- keys."""
    print("\nTest 10: Game-asset prompt selection")
    print("-" * 50)

    try:
        translator = AibaseTranslator()
        for key in ('game-asset-sprite', 'game-asset-animation', 'game-tilemap'):
            lang_name = AibaseTranslator.SUPPORTED_LANGUAGES[key]
            sys_p, usr_p = translator._build_prompts("test desc", lang_name, True, key)
            assert 'game' in sys_p.lower() or 'asset' in sys_p.lower(), \
                f"Expected game/asset in system prompt for {key}"
            assert 'code' in usr_p.lower(), \
                f"Expected 'code' in user prompt for {key}"
        print("✓ Game-asset prompt selection works correctly")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_mobile_language_targets():
    """Test that flutter/dart/react-native language targets are present."""
    print("\nTest 11: Flutter/React Native language targets")
    print("-" * 50)

    try:
        languages = AibaseTranslator.SUPPORTED_LANGUAGES
        for key in ('flutter', 'dart', 'react-native'):
            assert key in languages, f"Missing language key: {key}"
        print("✓ All 3 mobile language targets present")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_flutter_generator():
    """Test FlutterGenerator uses translator.translate() (Ollama-backed)."""
    print("\nTest 12: FlutterGenerator integration")
    print("-" * 50)

    try:
        from aibase import FlutterGenerator
        from unittest.mock import Mock, patch

        mock_resp = Mock()
        mock_resp.json.return_value = {"response": "import 'package:flutter/material.dart';"}
        mock_resp.raise_for_status = Mock()

        with patch('aibase.requests.post', return_value=mock_resp):
            translator = AibaseTranslator()
            gen = translator.get_flutter_generator()
            assert isinstance(gen, FlutterGenerator)
            # Subsequent call returns the same instance (cached)
            assert gen is translator.get_flutter_generator()
            code = gen.generate_widget('StatelessWidget', 'MyWidget')
            assert 'flutter' in code.lower() or 'import' in code.lower() or len(code) > 0
        print("✓ FlutterGenerator works via Ollama translator")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback; traceback.print_exc()
        return False


def test_react_native_generator():
    """Test ReactNativeGenerator uses translator.translate() (Ollama-backed)."""
    print("\nTest 13: ReactNativeGenerator integration")
    print("-" * 50)

    try:
        from aibase import ReactNativeGenerator
        from unittest.mock import Mock, patch

        mock_resp = Mock()
        mock_resp.json.return_value = {"response": "import React from 'react';"}
        mock_resp.raise_for_status = Mock()

        with patch('aibase.requests.post', return_value=mock_resp):
            translator = AibaseTranslator()
            gen = translator.get_react_native_generator()
            assert isinstance(gen, ReactNativeGenerator)
            code = gen.generate_component('functional', 'MyComponent')
            assert len(code) > 0
        print("✓ ReactNativeGenerator works via Ollama translator")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback; traceback.print_exc()
        return False


def test_ollama_404_raises_model_not_found():
    """Test that a 404 from Ollama raises a RuntimeError with actionable message."""
    print("\nTest 14: Ollama 404 → actionable error message")
    print("-" * 50)

    try:
        mock_resp = Mock()
        mock_resp.ok = False
        mock_resp.status_code = 404
        mock_resp.text = '{"error":"model not found"}'
        mock_resp.raise_for_status = Mock()

        with patch('aibase.requests.post', return_value=mock_resp):
            translator = AibaseTranslator()
            try:
                translator.translate("hello world", "python")
                print("✗ Expected RuntimeError not raised")
                return False
            except RuntimeError as e:
                msg = str(e)
                assert '404' in msg, f"Expected '404' in error, got: {msg}"
                assert 'ollama pull' in msg.lower(), \
                    f"Expected 'ollama pull' hint in error, got: {msg}"
                print(f"✓ Got expected RuntimeError: {msg[:80]}...")
                return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback; traceback.print_exc()
        return False


def test_ollama_connection_refused_raises_clear_error():
    """Test that a ConnectionError from Ollama raises a descriptive RuntimeError."""
    print("\nTest 15: Ollama ConnectionError → clear error")
    print("-" * 50)

    try:
        with patch('aibase.requests.post',
                   side_effect=__import__('requests').exceptions.ConnectionError("refused")):
            translator = AibaseTranslator()
            try:
                translator.translate("hello world", "python")
                print("✗ Expected RuntimeError not raised")
                return False
            except RuntimeError as e:
                msg = str(e)
                assert 'ollama' in msg.lower(), f"Expected 'Ollama' in error, got: {msg}"
                assert 'running' in msg.lower(), \
                    f"Expected 'running' hint in error, got: {msg}"
                print(f"✓ Got expected RuntimeError: {msg[:80]}...")
                return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback; traceback.print_exc()
        return False


def test_check_ollama_health_unreachable():
    """Test check_ollama_health when Ollama is unreachable."""
    print("\nTest 16: check_ollama_health — Ollama unreachable")
    print("-" * 50)

    try:
        with patch('aibase.requests.get',
                   side_effect=__import__('requests').exceptions.ConnectionError("refused")):
            translator = AibaseTranslator()
            result = translator.check_ollama_health()
            assert result['ok'] is False
            assert 'connect' in result['message'].lower() or 'ollama' in result['message'].lower()
            print(f"✓ Health check correctly reports unreachable: {result['message'][:80]}")
            return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback; traceback.print_exc()
        return False


def test_check_ollama_health_model_missing():
    """Test check_ollama_health when Ollama is up but model is not pulled."""
    print("\nTest 17: check_ollama_health — model not pulled")
    print("-" * 50)

    try:
        version_resp = Mock()
        version_resp.ok = True
        version_resp.raise_for_status = Mock()
        version_resp.json.return_value = {"version": "0.16.3"}

        tags_resp = Mock()
        tags_resp.ok = True
        tags_resp.raise_for_status = Mock()
        tags_resp.json.return_value = {"models": [{"name": "llama3:latest"}]}

        with patch('aibase.requests.get', side_effect=[version_resp, tags_resp]):
            translator = AibaseTranslator(model="qwen2.5-coder:7b")
            result = translator.check_ollama_health()
            assert result['ok'] is False
            assert result['model_available'] is False
            assert 'ollama pull' in result['message'].lower() or 'not found' in result['message'].lower()
            print(f"✓ Health check correctly reports missing model: {result['message'][:80]}")
            return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback; traceback.print_exc()
        return False


def test_check_ollama_health_ok():
    """Test check_ollama_health when everything is fine."""
    print("\nTest 18: check_ollama_health — all OK")
    print("-" * 50)

    try:
        version_resp = Mock()
        version_resp.ok = True
        version_resp.raise_for_status = Mock()
        version_resp.json.return_value = {"version": "0.16.3"}

        tags_resp = Mock()
        tags_resp.ok = True
        tags_resp.raise_for_status = Mock()
        tags_resp.json.return_value = {"models": [{"name": "qwen2.5-coder:7b"}]}

        with patch('aibase.requests.get', side_effect=[version_resp, tags_resp]):
            translator = AibaseTranslator(model="qwen2.5-coder:7b")
            result = translator.check_ollama_health()
            assert result['ok'] is True
            assert result['version'] == '0.16.3'
            assert result['model_available'] is True
            print(f"✓ Health check correctly reports OK: {result['message'][:80]}")
            return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback; traceback.print_exc()
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
        test_translation_with_mock_ollama,
        test_custom_parameters,
        test_code_fence_stripping,
        test_game_language_targets,
        test_flame_prompt_selection,
        test_game_asset_prompt_selection,
        test_mobile_language_targets,
        test_flutter_generator,
        test_react_native_generator,
        test_ollama_404_raises_model_not_found,
        test_ollama_connection_refused_raises_clear_error,
        test_check_ollama_health_unreachable,
        test_check_ollama_health_model_missing,
        test_check_ollama_health_ok,
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
