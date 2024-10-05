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
