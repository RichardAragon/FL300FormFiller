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
    Queries the LLM model to complete the form data.
    """
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        prompt = f"Complete the following form details based on the given data: {form_data}"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        if response.status_code == 200:
            return response_data["choices"][0]["message"]["content"]
        else:
            print(f"Error from LLM: {response_data}")
            return {}
    except Exception as e:
        print(f"An error occurred while querying the LLM: {e}")
        return {}


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
            # Treat all values as strings to avoid numeric interpretation issues
            form_data[key] = request.form.get(key, '').strip()

        # Handle dynamic children information
        child_names = request.form.getlist('childName[]')
        child_dobs = request.form.getlist('childDOB[]')
        for i, (name, dob) in enumerate(zip(child_names, child_dobs), start=1):
            form_data[f'childName_{i}'] = name.strip()
            form_data[f'childDOB_{i}'] = dob.strip()

        # Query the LLM model to fill in additional form details
        llm_completion = get_llm_completion(form_data, api_key)
        if llm_completion:
            try:
                llm_data = json.loads(llm_completion)
                form_data.update(llm_data)
            except json.JSONDecodeError as e:
                print(f"Failed to parse LLM response: {e}")

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
