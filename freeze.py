# freeze.py
import sys
import traceback
from flask_frozen import Freezer
# Import the Flask app instance from app/__init__.py
from app import app

# --- Configuration for GitHub Pages ---
# Sets the base URL. CRITICAL for links/CSS/JS on GitHub Pages.
# Must match your repository name structure.
print("Setting FREEZER_BASE_URL to '/pyExplorer/'")
app.config['FREEZER_BASE_URL'] = '/pyExplorer/'

# Sets the output directory for the static files
app.config['FREEZER_DESTINATION'] = 'build'
# Keep .nojekyll file if generated by GitHub Actions
app.config['FREEZER_REMOVE_EXTRA_FILES'] = False

# --- Handling Dynamic URLs (IMPORTANT LIMITATION) ---
# Static site generation CANNOT dynamically create pages for every possible
# block, transaction, or address. We MUST provide examples/placeholders
# for Frozen-Flask to generate the *structure* of these pages.
# The actual *data* on these generated pages will only reflect
# what Flask renders for these specific placeholder values during the build.
# Features requiring real-time data or searching arbitrary hashes won't work fully.

freezer = Freezer(app)

@freezer.register_generator
def transaction_urls():
    print("Generating static structure for /tx/<hash> using placeholder.")
    # Provide one placeholder hash to generate the template structure
    yield {'tx_hash': 'placeholder_tx_hash'}

@freezer.register_generator
def block_urls():
    print("Generating static structure for /block/<hash> using placeholder.")
    # Provide one placeholder hash/number
    yield {'block_hash': 'placeholder_block_hash_or_number'}

@freezer.register_generator
def address_urls():
    print("Generating static structure for /address/<addr> using placeholder.")
    # Provide one placeholder address
    yield {'address': 'placeholder_address'}

# You might have other dynamic routes - add generators for them too!

# Main execution block for freezing
if __name__ == '__main__':
    print(f"Starting static site generation for pyExplorer...")
    print(f"Base URL: {app.config.get('FREEZER_BASE_URL', 'Not Set')}")
    print(f"Output directory: {app.config.get('FREEZER_DESTINATION', 'build')}")

    try:
        # This crawls your Flask app (using defined routes and generators)
        # and saves the output as static files.
        freezer.freeze()
        print(f"Static site generated successfully in '{app.config['FREEZER_DESTINATION']}'.")
        print("NOTE: Only placeholder pages were generated for dynamic routes (/tx, /block, /address).")
        print("Full dynamic explorer functionality requires a live backend or client-side fetching.")
    except Exception as e:
        print(f"\nERROR during freezing process: {e}\n", file=sys.stderr)
        if isinstance(e, ValueError) and 'URL generator' in str(e):
            print("This often means a dynamic route exists in Flask", file=sys.stderr)
            print("but lacks a corresponding @freezer.register_generator", file=sys.stderr)
            print("function in freeze.py to provide placeholder values.", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1) # Exit with error to fail the GitHub Action
