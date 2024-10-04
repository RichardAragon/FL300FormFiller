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
            'cself': request.form.get('cself', ''),
            'State': request.form.get('State', ''),
            'Zip': request.form.get('Zip', ''),
            'cnumber1': request.form.get('cnumber1', ''),
            'cnumber2': request.form.get('cnumber2', ''),
            'cemail': request.form.get('cemail', ''),
            'ccourt1': request.form.get('ccourt1', ''),
            'ccourt2': request.form.get('ccourt2', ''),
            'ccourt3': request.form.get('ccourt3', ''),
            'ccourt4': request.form.get('ccourt4', ''),
            'cpet1': request.form.get('cpet1', ''),
            'cdef1': request.form.get('cdef1', ''),
            'cop1': request.form.get('cop1', ''),
            'ccase': request.form.get('ccase', ''),
            'cresps1': request.form.get('cresps1', ''),
            'cdate1': request.form.get('cdate1', ''),
            'rfo.4': request.form.get('rfo_4', ''),
            'rfo.2': request.form.get('rfo_2', ''),
            'rfo.9': request.form.get('rfo_9', ''),
            'rfo.13': request.form.get('rfo_13', ''),
            'rfo.10': request.form.get('rfo_10', ''),
            'rfo.14': request.form.get('rfo_14', ''),
            'rfo15': request.form.get('rfo15', ''),
            'Text Field0': request.form.get('Text_Field0', ''),
            'Hearing.date': request.form.get('Hearing_date', ''),
            'Hearing.time': request.form.get('Hearing_time', ''),
            'Hearing.department': request.form.get('Hearing_department', ''),
            'Facts in Support': request.form.get('Facts_in_Support', ''),
            'rfo.cs.date': request.form.get('rfo_cs_date', ''),
            'rfo.cs.order': request.form.get('rfo_cs_order', ''),
            'dec.1.line17': request.form.get('dec_1_line17', ''),
            'cbox.mod': request.form.get('cbox_mod', ''),
            'dec.box.1.27': request.form.get('dec_box_1_27', ''),
            'My gross monthly income is.dec': request.form.get('My_gross_monthly_income_is_dec', ''),
            'rfo.cs.n1': request.form.get('rfo_cs_n1', ''),
            'rfo.m.1': request.form.get('rfo_m_1', ''),
            'rfo.cs.n2': request.form.get('rfo_cs_n2', ''),
            'rfo.m.2': request.form.get('rfo_m_2', ''),
            'Other Orders Requested': request.form.get('Other_Orders_Requested', ''),
            'rfo.1.3e': request.form.get('rfo_1_3e', ''),
            'servebox': request.form.get('servebox', ''),
            'otherparty': request.form.get('otherparty', ''),
            'Following are the facts regarding this circumstance 1.dec.1': request.form.get('Following_are_the_facts_regarding_this_circumstance_1_dec_1', ''),
            'Other circumstances exist that I am requesting the court to take into consideration in.dec.2.22': request.form.get('Other_circumstances_exist_that_I_am_requesting_the_court_to_take_into_consideration_in_dec_2_22', ''),
            'undefined_6.dec.2.19': request.form.get('undefined_6_dec_2_19', ''),
        }

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
