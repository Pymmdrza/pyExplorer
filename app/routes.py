from flask import render_template, request, jsonify, Response, redirect, url_for, send_file
from app import app
from datetime import datetime
import json
import queue
import threading
import re
import io
import time #Added this import
from weasyprint import HTML
from flask import Response, stream_with_context

from app.controllers.address_controller import get_address_details
from app.controllers.block_controller import get_block_details, get_blockchain_stats, get_blockchain_metrics
from app.controllers.transaction_controller import get_transaction_details
from app.utils.exports import export_to_json, export_to_csv, format_transaction_data, format_address_data

# Initialize transaction queue
latest_transactions = queue.Queue(maxsize=100)  # Keep last 100 transactions

def handle_new_transaction(tx):
    if latest_transactions.full():
        latest_transactions.get()  # Remove oldest transaction if queue is full
    latest_transactions.put(tx)

@app.route('/')
def index():
    try:
        # Get blockchain statistics and metrics
        stats = get_blockchain_stats()
        metrics = get_blockchain_metrics()
        return render_template('index.html', stats=stats, metrics=metrics)
    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}")
        return render_template('error.html', message='An error occurred while loading the page'), 500

@app.route('/search')
def search():
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({'error': 'Missing search query'}), 400

        query_type = detect_query_type(query)
        if query_type == 'transaction':
            return redirect(url_for('transaction', tx_hash=query))
        elif query_type == 'address':
            return redirect(url_for('address', address=query))
        elif query_type == 'block':
            return redirect(url_for('block', height=int(query)))
        else:
            return render_template('error.html', 
                          message='Invalid search query format. Please enter a valid transaction hash, address, or block number.'), 400
    except Exception as e:
        app.logger.error(f"Error in search route: {str(e)}")
        return render_template('error.html', message='An error occurred while processing your search'), 500

@app.route('/block/<height>')
@app.route('/block/<height>/page/<int:page>')
def block(height, page=1):
    try:
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    try:
        block_data = get_block_details(height, page)
        if block_data is None:
            return render_template('error.html', message='Block not found'), 404
        return render_template('block.html', block=block_data, datetime=datetime)
    except Exception as e:
        app.logger.error(f"Error in block route: {str(e)}")
        return render_template('error.html', message='An error occurred while loading block details'), 500

@app.route('/address/<string:address>')
@app.route('/address/<string:address>/page/<int:page>')
def address(address, page=1):
    try:
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    try:
        address_data = get_address_details(address, page)
        if address_data is None:
            return render_template('error.html', message='Address not found'), 404
        return render_template('address.html', address=address_data, datetime=datetime)
    except Exception as e:
        app.logger.error(f"Error in address route: {str(e)}")
        return render_template('error.html', message='An error occurred while loading address details'), 500

@app.route('/tx/<string:tx_hash>')
def transaction(tx_hash):
    try:
        tx_data = get_transaction_details(tx_hash)
        if tx_data is None:
            return render_template('error.html', message='Transaction not found'), 404
        return render_template('transaction.html', transaction=tx_data)
    except Exception as e:
        app.logger.error(f"Error in transaction route: {str(e)}")
        return render_template('error.html', message='An error occurred while loading transaction details'), 500


@app.route('/tx/<string:tx_hash>/export/<string:format>')
def export_transaction(tx_hash, format):
    try:
        tx_data = get_transaction_details(tx_hash)
        if tx_data is None:
            return render_template('error.html', message='Transaction not found'), 404

        formatted_data = format_transaction_data(tx_data)

        if format == 'json':
            response = Response(
                export_to_json(formatted_data),
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment;filename=transaction-{tx_hash[:8]}.json'}
            )
        elif format == 'csv':
            response = Response(
                export_to_csv(formatted_data, 'transaction'),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment;filename=transaction-{tx_hash[:8]}.csv'}
            )
        else:
            return render_template('error.html', message='Invalid export format'), 400

        return response
    except Exception as e:
        app.logger.error(f"Error in export_transaction route: {str(e)}")
        return render_template('error.html', message='An error occurred while exporting transaction data'), 500

@app.route('/address/<string:address>/export/<string:format>')
def export_address(address, format):
    try:
        address_data = get_address_details(address)
        if address_data is None:
            return render_template('error.html', message='Address not found'), 404

        formatted_data = format_address_data(address_data)

        if format == 'json':
            response = Response(
                export_to_json(formatted_data),
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment;filename=address-{address[:8]}.json'}
            )
        elif format == 'csv':
            response = Response(
                export_to_csv(formatted_data, 'address'),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment;filename=address-{address[:8]}.csv'}
            )
        else:
            return render_template('error.html', message='Invalid export format'), 400

        return response
    except Exception as e:
        app.logger.error(f"Error in export_address route: {str(e)}")
        return render_template('error.html', message='An error occurred while exporting address data'), 500

@app.route('/tx/<string:tx_hash>/receipt')
def transaction_receipt(tx_hash):
    try:
        tx_data = get_transaction_details(tx_hash)
        if tx_data is None:
            return render_template('error.html', message='Transaction not found'), 404

        html = render_template('transaction_receipt.html',
                             transaction=tx_data,
                             now=datetime.utcnow())

        pdf = HTML(string=html).write_pdf()

        response = send_file(
            io.BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'transaction-{tx_hash[:8]}.pdf'
        )

        return response
    except Exception as e:
        app.logger.error(f"Error in transaction_receipt route: {str(e)}")
        return render_template('error.html', message='An error occurred while generating transaction receipt'), 500

def detect_query_type(query):
    """
    Detect the type of query based on its pattern
    """
    query = query.strip().lower()

    # Bitcoin address pattern (starts with 1, 3, or bc1)
    if re.match(r'^(1|3|bc1)[a-zA-Z0-9]{25,39}$', query):
        return 'address'

    # Transaction hash pattern (64 hex characters)
    if re.match(r'^[a-f0-9]{64}$', query):
        return 'transaction'

    # Block height pattern (numeric)
    if re.match(r'^\d+$', query):
        return 'block'

    return None

@app.route('/transactions/stream')
def stream_transactions():
    def generate():
        while True:
            # Send a ping every 30 seconds to keep connection alive
            yield "data: {\"ping\": true}\n\n"
            try:
                # Get new transaction without blocking
                tx = latest_transactions.get_nowait()
                yield f"data: {json.dumps(tx)}\n\n"
            except queue.Empty:
                pass
            time.sleep(1)  # Sleep for a second before next check

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )