#!/usr/bin/env python3
"""
Aibase API Server
REST API interface for the AI code translator
"""

import os
import socket
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from aibase import AibaseTranslator

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.after_request
def skip_ngrok_browser_warning(response):
    """Tell ngrok to skip the browser interstitial warning page.

    Without this, free-tier ngrok tunnels show a warning page to browser
    visitors before redirecting them to the actual site.  Adding this header
    to every response bypasses that page so friends can open the shared URL
    directly.
    """
    response.headers['ngrok-skip-browser-warning'] = '1'
    return response

# Initialize translator
translator = None

def get_translator():
    """Get or create translator instance."""
    global translator
    if translator is None:
        translator = AibaseTranslator()
    return translator


def validate_request_data(data, required_fields):
    """
    Validate request data has required fields.

    Args:
        data (dict): Request data
        required_fields (list): List of required field names

    Returns:
        tuple: (is_valid, error_message)
    """
    if not data:
        return False, 'No JSON data provided'

    for field in required_fields:
        if field not in data or not data[field]:
            return False, f'{field} is required'

    return True, None


@app.route('/', methods=['GET'])
def index():
    """Serve the Aibase web UI."""
    return render_template('index.html')


@app.route('/api/info', methods=['GET'])
def api_info():
    """JSON description of available API endpoints."""
    return jsonify({
        'name': 'Aibase API',
        'version': '1.0.0',
        'description': 'AI-powered Natural Language to Code Translator',
        'endpoints': {
            'POST /api/translate': 'Translate natural language to code',
            'GET /api/languages': 'Get list of supported languages',
            'GET /api/health': 'Health check endpoint',
            'POST /api/generate/flutter/widget': 'Generate Flutter widget',
            'POST /api/generate/flutter/screen': 'Generate Flutter screen',
            'POST /api/generate/flutter/app': 'Generate Flutter app',
            'POST /api/generate/react-native/component': 'Generate React Native component',
            'POST /api/generate/react-native/screen': 'Generate React Native screen',
            'POST /api/generate/react-native/app': 'Generate React Native app boilerplate',
        }
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'aibase-api'
    })


@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get list of supported programming languages."""
    langs = AibaseTranslator.SUPPORTED_LANGUAGES
    return jsonify({
        'languages': list(langs.keys()),
        'names': langs,
        'count': len(langs)
    })


@app.route('/api/translate', methods=['POST'])
def translate():
    """
    Translate natural language description to code.
    
    Request body:
    {
        "description": "natural language description",
        "language": "python",       // optional, defaults to python
        "include_comments": true,   // optional, defaults to true
        "model": "qwen2.5-coder:7b", // optional, overrides OLLAMA_MODEL
        "temperature": 0.7,         // optional
        "max_tokens": 2000          // optional
    }
    
    Response:
    {
        "success": true,
        "code": "generated code",
        "language": "python"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        description = data.get('description')
        if not description:
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400
        
        # Get optional parameters
        language = data.get('language', 'python')
        include_comments = data.get('include_comments', True)
        model = data.get('model')
        temperature = data.get('temperature')
        max_tokens = data.get('max_tokens')
        
        # Validate language
        if language.lower() not in AibaseTranslator.SUPPORTED_LANGUAGES:
            return jsonify({
                'success': False,
                'error': f'Unsupported language: {language}',
                'supported_languages': list(AibaseTranslator.SUPPORTED_LANGUAGES.keys())
            }), 400
        
        # Get or create translator with custom parameters if provided
        if model or temperature is not None or max_tokens is not None:
            trans = AibaseTranslator(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            trans = get_translator()
        
        # Generate code
        code = trans.translate(
            description=description,
            target_language=language,
            include_comments=include_comments
        )
        
        # Return success response
        return jsonify({
            'success': True,
            'code': code,
            'language': language
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except RuntimeError as e:
        app.logger.error(f"Translation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 503
    except Exception as e:
        app.logger.error(f"Translation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== Flutter Generation Endpoints ==========

@app.route('/api/generate/flutter/widget', methods=['POST'])
def generate_flutter_widget():
    """
    Generate Flutter widget code.

    Request body:
    {
        "widget_type": "StatelessWidget",
        "name": "MyWidget",
        "properties": {"title": "String"},       // optional
        "state_requirements": {"counter": "int"} // optional
    }
    """
    try:
        data = request.get_json()
        is_valid, error_msg = validate_request_data(data, ['widget_type', 'name'])
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400

        trans = get_translator()
        code = trans.get_flutter_generator().generate_widget(
            widget_type=data['widget_type'],
            name=data['name'],
            properties=data.get('properties'),
            state_requirements=data.get('state_requirements'),
        )
        return jsonify({'success': True, 'code': code, 'widget_name': data['name']})

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 422
    except RuntimeError as e:
        app.logger.error(f"Flutter widget generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        app.logger.error(f"Flutter widget generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate/flutter/screen', methods=['POST'])
def generate_flutter_screen():
    """
    Generate a complete Flutter screen.

    Request body:
    {
        "screen_name": "HomeScreen",
        "widgets": ["AppBar", "ListView"],  // optional
        "navigation_setup": {"type": "named"} // optional
    }
    """
    try:
        data = request.get_json()
        is_valid, error_msg = validate_request_data(data, ['screen_name'])
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400

        trans = get_translator()
        code = trans.get_flutter_generator().generate_screen(
            screen_name=data['screen_name'],
            widgets=data.get('widgets'),
            navigation_setup=data.get('navigation_setup'),
        )
        return jsonify({'success': True, 'code': code, 'screen_name': data['screen_name']})

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 422
    except RuntimeError as e:
        app.logger.error(f"Flutter screen generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        app.logger.error(f"Flutter screen generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate/flutter/app', methods=['POST'])
def generate_flutter_app():
    """
    Generate Flutter app boilerplate.

    Request body:
    {
        "app_name": "MyApp",
        "theme": {"primaryColor": "blue"}, // optional
        "initial_route": "/home"           // optional
    }
    """
    try:
        data = request.get_json()
        is_valid, error_msg = validate_request_data(data, ['app_name'])
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400

        trans = get_translator()
        code = trans.get_flutter_generator().generate_app(
            app_name=data['app_name'],
            theme=data.get('theme'),
            initial_route=data.get('initial_route'),
        )
        return jsonify({'success': True, 'code': code, 'app_name': data['app_name']})

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 422
    except RuntimeError as e:
        app.logger.error(f"Flutter app generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        app.logger.error(f"Flutter app generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== React Native Generation Endpoints ==========

@app.route('/api/generate/react-native/component', methods=['POST'])
def generate_react_native_component():
    """
    Generate React Native component.

    Request body:
    {
        "component_type": "functional",
        "name": "MyComponent",
        "props": {"title": "string"},   // optional
        "hooks_needed": ["useState"]    // optional
    }
    """
    try:
        data = request.get_json()
        is_valid, error_msg = validate_request_data(data, ['component_type', 'name'])
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400

        trans = get_translator()
        code = trans.get_react_native_generator().generate_component(
            component_type=data['component_type'],
            name=data['name'],
            props=data.get('props'),
            hooks_needed=data.get('hooks_needed'),
        )
        return jsonify({'success': True, 'code': code, 'component_name': data['name']})

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 422
    except RuntimeError as e:
        app.logger.error(f"React Native component generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        app.logger.error(f"React Native component generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate/react-native/screen', methods=['POST'])
def generate_react_native_screen():
    """
    Generate a complete React Native screen.

    Request body:
    {
        "screen_name": "HomeScreen",
        "components": ["Header", "Footer"],   // optional
        "navigation_setup": {"type": "stack"} // optional
    }
    """
    try:
        data = request.get_json()
        is_valid, error_msg = validate_request_data(data, ['screen_name'])
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400

        trans = get_translator()
        code = trans.get_react_native_generator().generate_screen(
            screen_name=data['screen_name'],
            components=data.get('components'),
            navigation_setup=data.get('navigation_setup'),
        )
        return jsonify({'success': True, 'code': code, 'screen_name': data['screen_name']})

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 422
    except RuntimeError as e:
        app.logger.error(f"React Native screen generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        app.logger.error(f"React Native screen generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate/react-native/app', methods=['POST'])
def generate_react_native_app():
    """
    Generate React Native app boilerplate.

    Request body:
    {
        "app_name": "MyApp",
        "typescript": true,        // optional, default true
        "initial_screen": "Home"   // optional
    }
    """
    try:
        data = request.get_json()
        is_valid, error_msg = validate_request_data(data, ['app_name'])
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400

        trans = get_translator()
        code = trans.get_react_native_generator().generate_app(
            app_name=data['app_name'],
            typescript=data.get('typescript', True),
            initial_screen=data.get('initial_screen'),
        )
        return jsonify({'success': True, 'code': code, 'app_name': data['app_name']})

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 422
    except RuntimeError as e:
        app.logger.error(f"React Native app generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        app.logger.error(f"React Native app generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


def get_local_ip():
    """Return the machine's primary local-network IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except OSError:
        return None


def check_provider_config():
    """Return a status string about the Ollama configuration for the startup banner."""
    ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    model = os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:7b')
    return (
        f'  Provider:       Ollama  ✓ (free, no API key needed)\n'
        f'  Ollama URL:     {ollama_url}\n'
        f'  Model:          {model}'
    )


def start_ngrok_tunnel(port):
    """
    Open a public ngrok HTTPS tunnel to *port* using pyngrok.

    If NGROK_DOMAIN is set in the environment (or .env), ngrok will bind to
    that static/reserved domain (e.g. costless-dorthy-unmeanderingly.ngrok-free.dev)
    so the URL is always the same across restarts.

    Returns the public URL string on success, or None with a printed
    error message if pyngrok is not installed or the tunnel fails.
    """
    try:
        from pyngrok import ngrok, conf

        # Use authtoken from environment if provided
        authtoken = os.getenv('NGROK_AUTHTOKEN')
        if authtoken:
            conf.get_default().auth_token = authtoken

        # Use a reserved/static domain if one is configured
        domain = os.getenv('NGROK_DOMAIN')
        options = {}
        if domain:
            options['domain'] = domain

        tunnel = ngrok.connect(port, "http", bind_tls=True, **options)
        return tunnel.public_url
    except ImportError:
        print(
            "\n  ⚠  pyngrok is not installed. Run:\n"
            "       pip install pyngrok\n"
            "  then restart the server.\n"
        )
        return None
    except Exception as exc:
        print(f"\n  ⚠  Could not start ngrok tunnel: {exc}\n")
        return None


def main():
    """Run the API server."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Aibase API Server - REST API for AI code translation'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind the server to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run the server on (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    parser.add_argument(
        '--ngrok', '--ngrokk',   # accept common typo --ngrokk
        dest='ngrok',
        action='store_true',
        help=(
            'Open a public ngrok tunnel so anyone on the internet can access '
            'the server. Requires pyngrok (pip install pyngrok). Optionally '
            'set NGROK_AUTHTOKEN in .env for longer sessions.'
        )
    )

    args = parser.parse_args()

    local_ip = get_local_ip()
    lan_line = (
        f"  Local network:  http://{local_ip}:{args.port}/\n  (anyone on your Wi-Fi/LAN can use this URL)"
        if local_ip else
        "  Local network:  (could not detect local IP)"
    )

    # Start ngrok tunnel before Flask so the URL is ready to print
    ngrok_url = None
    if args.ngrok:
        print("  Starting ngrok tunnel…", flush=True)
        ngrok_url = start_ngrok_tunnel(args.port)

    if ngrok_url:
        ngrok_line = (
            f"  🌍 Public URL:   {ngrok_url}\n"
            f"  Share this link with anyone — no router setup needed!\n\n"
            f"  ⚠️  IMPORTANT: This window must stay open.\n"
            f"  If you close this terminal, the link stops working (HTTP 404).\n"
            f"  Your friend will see a 404 error if the server is not running."
        )
    else:
        ngrok_line = "  Public URL:     (ngrok not active — run with --ngrok to enable)"

    provider_info = check_provider_config()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    Aibase API Server                         ║
╚══════════════════════════════════════════════════════════════╝

{provider_info}

Server running!  Open one of these URLs in a browser:

  This computer:  http://localhost:{args.port}/
{lan_line}
{ngrok_line}

Debug mode: {args.debug}

Endpoints:
  GET  /                   - Web UI (browser)
  GET  /api/info           - API information (JSON)
  GET  /api/health         - Health check
  GET  /api/languages      - List supported languages
  POST /api/translate      - Translate natural language to code

  Flutter Generation:
  POST /api/generate/flutter/widget          - Generate Flutter widget
  POST /api/generate/flutter/screen          - Generate Flutter screen
  POST /api/generate/flutter/app             - Generate Flutter app

  React Native Generation:
  POST /api/generate/react-native/component  - Generate React Native component
  POST /api/generate/react-native/screen     - Generate React Native screen
  POST /api/generate/react-native/app        - Generate React Native app

Press Ctrl+C to stop the server
""")
    
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\n\nError starting server: {e}")


if __name__ == '__main__':
    main()
