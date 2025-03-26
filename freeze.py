# freeze.py
import sys
import traceback
from flask_frozen import Freezer
# Import the Flask app instance from app/__init__.py
from app import app

# --- Configuration for GitHub Pages ---
print("Setting FREEZER_BASE_URL to '/'")
app.config['FREEZER_BASE_URL'] = '/'
app.config['FREEZER_DESTINATION'] = './build'
app.config['FREEZER_REMOVE_EXTRA_FILES'] = False
# app.config['FREEZER_FOLLOW_REDIRECTS'] = True # May not be needed if we ignore /search

# *** ADD THIS LINE TO IGNORE THE /search ENDPOINT ***
# 'search' is the function name associated with the @app.route('/search') decorator
app.config['FREEZER_IGNORE_ENDPOINTS'] = ['search']
print("Ignoring endpoint 'search' during freeze.")
# -------------------------------------------------------

# --- Handling Dynamic URLs ---
freezer = Freezer(app)

@freezer.register_generator
def transaction_urls():
    print("Generating static structure for /tx/<hash> using placeholder.")
    yield {'tx_hash': 'placeholder_tx_hash'}

@freezer.register_generator
def block_urls():
    print("Generating static structure for /block/<height> using placeholder.")
    # Note: Your route uses height, not block_hash
    yield {'height': 0} # Use 0 or another placeholder block number

@freezer.register_generator
def address_urls():
    print("Generating static structure for /address/<addr> using placeholder.")
    yield {'address': 'placeholder_address'}

# Main execution block for freezing
if __name__ == '__main__':
    print(f"Starting static site generation for pyExplorer...")
    print(f"Base URL: {app.config.get('FREEZER_BASE_URL', 'Not Set')}")
    print(f"Output directory: {app.config.get('FREEZER_DESTINATION', 'build')}")

    try:
        freezer.freeze()
        print(f"Static site generated successfully in '{app.config['FREEZER_DESTINATION']}'.")
        print("NOTE: Only placeholder pages were generated for dynamic routes (/tx, /block, /address).")
        print("NOTE: The /search endpoint itself was skipped during generation.")
    except Exception as e:
        print(f"\nERROR during freezing process: {e}\n", file=sys.stderr)
        if isinstance(e, ValueError) and 'URL generator' in str(e):
            print("This often means a dynamic route exists in Flask", file=sys.stderr)
            print("but lacks a corresponding @freezer.register_generator", file=sys.stderr)
            print("function in freeze.py to provide placeholder values.", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1) # Exit with error to fail the GitHub Action
