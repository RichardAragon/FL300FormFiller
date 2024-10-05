import os
import fitz  # PyMuPDF
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)

# Use environment variable for secret key
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Directory to store filled PDFs temporarily
FILLED_FORMS_DIR = 'filled_forms'
os.makedirs(FILLED_FORMS_DIR, exist_ok=True)

# Path to the input PDF form
INPUT_PDF_PATH = os.path.join('input_forms', 'FL-300_Form_Template.pdf')  # Ensure this path is correct

def fill_form(pdf_path, form_data):
    """
    Fills the PDF form with the provided form data.
    """
    doc = fitz.open(pdf_path)
    for page_num, page in enumerate(doc):
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                field_name = widget.field_name
                if field_name in form_data:
                    widget.field_value = form_data[field_name]
                    widget.update()
    # Save to a BytesIO object to avoid writing to disk
    pdf_bytes = BytesIO()
    doc.save(pdf_bytes)
    doc.close()
    pdf_bytes.seek(0)
    return pdf_bytes

@app.route('/', methods=['GET'])
def index():
    return render_template('form.html')

@app.route('/fill_form', methods=['POST'])
def fill_form_route():
    try:
        # Extract form data from the submitted form
        form_data = {
            'Your Full Name': request.form.get('your_name', ''),
            'Street Address': request.form.get('your_address', ''),
            'City': request.form.get('your_city', ''),
            'State': request.form.get('your_state', ''),
            'Zip Code': request.form.get('your_zip', ''),
            'Phone Number': request.form.get('your_phone', ''),
            'Email Address': request.form.get('your_email', ''),
            'Representation': request.form.get('self_represented', ''),
            'Court Name': request.form.get('court_name', ''),
            'Court Street Address': request.form.get('court_street_address', ''),
            'Court City': request.form.get('court_city', ''),
            'Court State': request.form.get('court_state', ''),
            'Court Zip Code': request.form.get('court_zip', ''),
            'Court Branch Name': request.form.get('court_branch_name', ''),
            'Petitioner Name': request.form.get('petitioner_name', ''),
            'Respondent Name': request.form.get('respondent_name', ''),
            'Other Party Name': request.form.get('other_party_name', ''),
            'Your Role': request.form.get('your_role', ''),
            'Case Number': request.form.get('case_number', ''),
            'Facts in Support': request.form.get('facts_support', ''),
            'Signature Date': request.form.get('signature_date', ''),
            'Signature Name': request.form.get('signature_name', ''),
            # Orders Requested
            'Order Child Custody': 'Yes' if request.form.get('order_child_custody') else 'Off',
            'Order Child Visitation': 'Yes' if request.form.get('order_child_visitation') else 'Off',
            'Order Child Support': 'Yes' if request.form.get('order_child_support') else 'Off',
            'Order Spousal Support': 'Yes' if request.form.get('order_spousal_support') else 'Off',
            'Order Property Control': 'Yes' if request.form.get('order_property_control') else 'Off',
            'Order Attorney Fees': 'Yes' if request.form.get('order_attorney_fees') else 'Off',
            'Order Other': 'Yes' if request.form.get('order_other') else 'Off',
            'Order Other Specify': request.form.get('order_other_specify', ''),
        }

        # Fill the form with the provided data
        pdf_bytes = fill_form(INPUT_PDF_PATH, form_data)

        # Send the filled PDF as a downloadable file
        return send_file(
            pdf_bytes,
            as_attachment=True,
            attachment_filename='FL-300_Filled.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"An error occurred: {e}")
        flash("An unexpected error occurred while processing your request.", "danger")
        return redirect(url_for('index'))

if __name__ == "__main__":
    # Set debug to False for production
    app.run(debug=False)
