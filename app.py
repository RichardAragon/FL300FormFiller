import os
import fitz  # PyMuPDF
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from io import BytesIO

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
    doc = fitz.open(pdf_path)
    for page_num, page in enumerate(doc):
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                field_name = widget.field_name
                if field_name in form_data:
                    widget.field_value = form_data[field_name]
                    widget.update()
    doc.save(output_path)
    doc.close()

@app.route('/', methods=['GET'])
def index():
    return render_template('form.html')

@app.route('/fill_form', methods=['POST'])
def fill_form_route():
    try:
        # Extract form data from the submitted form
        form_data = {
            'cname1': request.form.get('cname1', ''),
            'cname2': request.form.get('cname2', ''),
            'cname3': request.form.get('cname3', ''),
            'cname4': request.form.get('cname4', ''),
            'State': request.form.get('State', ''),
            'Zip': request.form.get('Zip', ''),
            'cnumber1': request.form.get('cnumber1', ''),
            'cemail': request.form.get('cemail', ''),
            'ccourt1': request.form.get('ccourt1', ''),
            'ccourt2': request.form.get('ccourt2', ''),
            'ccourt3': request.form.get('ccourt3', ''),
            'cpet1': request.form.get('cpet1', ''),
            'cdef1': request.form.get('cdef1', ''),
            'ccase': request.form.get('ccase', ''),
            'cdate1': request.form.get('cdate1', ''),
            'Text_Field0': request.form.get('Text_Field0', ''),
            'monthlyIncome': request.form.get('monthlyIncome', ''),
            'otherParentMonthlyIncome': request.form.get('otherParentMonthlyIncome', ''),
            'Facts_in_Support': request.form.get('Facts_in_Support', ''),
            'rfo_4': request.form.get('rfo_4', ''),
            'rfo_2': request.form.get('rfo_2', ''),
            'rfo_9': request.form.get('rfo_9', ''),
            'rfo_13': request.form.get('rfo_13', ''),
            'rfo_10': request.form.get('rfo_10', ''),
            'rfo_14': request.form.get('rfo_14', ''),
            # Additional fields from the form
            'iefilltext1f': request.form.get('iefilltext1f', ''),
            'iefilltext2a': request.form.get('iefilltext2a', ''),
            'iefilltext2b': request.form.get('iefilltext2b', ''),
            'iefilltext3a1': request.form.get('iefilltext3a1', ''),
            'iefilltext3b1': request.form.get('iefilltext3b1', ''),
            'iefilltext4a': request.form.get('iefilltext4a', ''),
            'iefilltext5a1': request.form.get('iefilltext5a1', ''),
            'iefilltext5b1': request.form.get('iefilltext5b1', ''),
            'iefilltext6a1': request.form.get('iefilltext6a1', ''),
            'iefilltext6b1': request.form.get('iefilltext6b1', ''),
            'iefilltext7a': request.form.get('iefilltext7a', ''),
            'iefilltext8': request.form.get('iefilltext8', ''),
            'iefilltext9': request.form.get('iefilltext9', ''),
            'iefilltext10a': request.form.get('iefilltext10a', ''),
            'iefilltext11a': request.form.get('iefilltext11a', ''),
            'iefilltext12a1': request.form.get('iefilltext12a1', ''),
            'CheckBox31': request.form.get('CheckBox31', ''),
            'iecheckbox2b1': request.form.get('iecheckbox2b1', ''),
            'iecheckbox3a1': request.form.get('iecheckbox3a1', ''),
            'iecheckbox5d1': request.form.get('iecheckbox5d1', ''),
        }

        # Handle dynamic children information
        child_names = request.form.getlist('childName[]')
        child_dobs = request.form.getlist('childDOB[]')
        for i, (name, dob) in enumerate(zip(child_names, child_dobs), start=1):
            form_data[f'childName_{i}'] = name
            form_data[f'childDOB_{i}'] = dob

        # Generate a unique filename for the filled PDF
        filled_pdf_filename = secure_filename(f"filled_form_{os.urandom(8).hex()}.pdf")
        output_pdf_path = os.path.join(FILLED_FORMS_DIR, filled_pdf_filename)

        # Fill the form with the provided data
        fill_form(INPUT_PDF_PATH, output_pdf_path, form_data)

        # Send the filled PDF as a downloadable file
        return send_file(output_pdf_path, as_attachment=True)

    except Exception as e:
        print(f"An error occurred: {e}")
        flash("An unexpected error occurred while processing your request.", "danger")
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
