import os
import fitz  # PyMuPDF
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from io import BytesIO
from form_fields import form_fields  # Ensure this import is correct
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key

# Directory to store filled PDFs temporarily
FILLED_FORMS_DIR = 'filled_forms'
os.makedirs(FILLED_FORMS_DIR, exist_ok=True)

# Path to the input PDF form
INPUT_PDF_PATH = os.path.join('input_forms', 'Xfa_FL300_filled+(1).pdf')  # Ensure this path is correct

def fill_form(pdf_path, output_path, form_data):
    """
    Fills the PDF form with the provided form data.
    """
    logging.debug(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    for page_num, page in enumerate(doc):
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                field_name = widget.field_name
                logging.debug(f"Processing widget: {field_name}")
                if field_name in form_fields:
                    web_form_field = form_fields[field_name]
                    if web_form_field in form_data:
                        value = form_data[web_form_field]
                        logging.debug(f"Setting PDF field '{field_name}' to '{value}'")
                        widget.field_value = value
                        widget.update()
    doc.save(output_path)
    logging.debug(f"Saved filled PDF to: {output_path}")
    doc.close()

@app.route('/', methods=['GET'])
def index():
    return render_template('form.html')

@app.route('/fill_form', methods=['POST'])
def fill_form_route():
    try:
        # Dynamically build form_data using form_fields mapping
        form_data = {}
        for pdf_field, web_field in form_fields.items():
            value = request.form.get(web_field, '')
            form_data[web_field] = value
            logging.debug(f"Retrieved form data: {web_field} = {value}")

        # Handle dynamic children information
        child_names = request.form.getlist('child_name[]')  # Ensure this matches your HTML form
        child_dobs = request.form.getlist('child_date_of_birth[]')  # Ensure this matches your HTML form
        for i, (name, dob) in enumerate(zip(child_names, child_dobs), start=1):
            form_data[f'child_name_{i}'] = name
            form_data[f'child_date_of_birth_{i}'] = dob
            logging.debug(f"Child {i}: name = {name}, DOB = {dob}")

        # Debugging: Print form_data to verify
        logging.debug(f"Final form_data: {form_data}")

        # Generate a unique filename for the filled PDF
        filled_pdf_filename = secure_filename(f"filled_form_{os.urandom(8).hex()}.pdf")
        output_pdf_path = os.path.join(FILLED_FORMS_DIR, filled_pdf_filename)

        # Fill the form with the provided data
        fill_form(INPUT_PDF_PATH, output_pdf_path, form_data)

        # Send the filled PDF as a downloadable file
        logging.debug("Sending filled PDF to user.")
        return send_file(output_pdf_path, as_attachment=True)

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        flash("An unexpected error occurred while processing your request.", "danger")
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
