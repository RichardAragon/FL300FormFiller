import os
import fitz  # PyMuPDF
import requests
import json
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename

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
    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Input PDF form not found at: {pdf_path}")

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
    except Exception as e:
        print(f"Error while filling the form: {e}")
        raise


def get_llm_completion(form_data, api_key):
    """
    Queries the LLM model to complete the form data by filling in any missing information based on the provided data.
    """
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Prepare the prompt that instructs the model to fill missing fields without making up new information.
        instructions = (
            "You are filling in a form. Based on the given data, complete any missing fields by logically "
            "filling them with appropriate values if possible. Do not create values for missing fields unless the data "
            "provided can logically fill them. Use the field names given in the following data:"
        )
        prompt = f"{instructions}\n\nForm Data: {json.dumps(form_data, indent=2)}"
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        # Make the request to the OpenAI API
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()

        if response.status_code == 200:
            completion_text = response_data["choices"][0]["message"]["content"]
            return completion_text
        else:
            print(f"Error from LLM: {response_data}")
            return None
    except Exception as e:
        print(f"An error occurred while querying the LLM: {e}")
        return None


@app.route('/', methods=['GET'])
def index():
    return render_template('form.html')


@app.route('/fill_form', methods=['POST'])
def fill_form_route():
    try:
        # Extract OpenAI API key from the submitted form
        api_key = request.form.get('openai_api_key', '')
        if not api_key:
            flash("OpenAI API key is required to complete the form.", "danger")
            return redirect(url_for('index'))

        # Extract form data from the submitted form
        form_data = {}
        for key in request.form.keys():
            if key == 'openai_api_key':
                continue
            form_data[key] = request.form.get(key, '').strip()

        # Handle dynamic children information
        child_names = request.form.getlist('childName[]')
        child_dobs = request.form.getlist('childDOB[]')
        for i, (name, dob) in enumerate(zip(child_names, child_dobs), start=1):
            form_data[f'childName_{i}'] = name.strip()
            form_data[f'childDOB_{i}'] = dob.strip()

        # Define the form fields expected to be filled
        expected_fields = [
            "caseType", "cname1", "cname2", "cname3", "cname4", "State", "Zip",
            "cnumber1", "cemail", "ccourt1", "ccourt2", "ccourt3", "cpet1", "cdef1",
            "ccase", "monthlyIncome", "otherParentMonthlyIncome", "Facts_in_Support",
            "cdate1", "Text_Field0", "iefilltext1f", "iefilltext2a", "iefilltext3a1", 
            "CheckBox31", "rfo_4", "rfo_2", "rfo_9", "rfo_13", "rfo_10", "rfo_14"
        ]

        # Add expected fields that may have been missed in dynamic extraction
        for field in expected_fields:
            if field not in form_data:
                form_data[field] = request.form.get(field, '').strip()

        # Query the LLM model to fill in additional form details
        llm_completion = get_llm_completion(form_data, api_key)
        if llm_completion:
            try:
                # Parse the LLM response as JSON and merge it with the current form data
                llm_data = json.loads(llm_completion)
                form_data.update(llm_data)
            except json.JSONDecodeError as e:
                print(f"Failed to parse LLM response: {e}")
                flash("Failed to process the LLM response.", "danger")
                return redirect(url_for('index'))

        # Generate a unique filename for the filled PDF
        filled_pdf_filename = secure_filename(f"filled_form_{os.urandom(8).hex()}.pdf")
        output_pdf_path = os.path.join(FILLED_FORMS_DIR, filled_pdf_filename)

        # Fill the form with the provided data
        fill_form(INPUT_PDF_PATH, output_pdf_path, form_data)

        # Send the filled PDF as a downloadable file
        if os.path.exists(output_pdf_path):
            return send_file(output_pdf_path, as_attachment=True)
        else:
            flash("An unexpected error occurred while creating the filled PDF.", "danger")
            return redirect(url_for('index'))

    except Exception as e:
        print(f"An error occurred: {e}")
        flash("An unexpected error occurred while processing your request.", "danger")
        return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
