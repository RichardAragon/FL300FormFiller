// app.js

// Load environment variables from .env file
require('dotenv').config();

// Import required modules
const express = require('express');
const multer = require('multer');
const { PDFDocument } = require('pdf-lib');
const fs = require('fs');
const path = require('path');
const bodyParser = require('body-parser');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const csrf = require('csurf');
const cookieParser = require('cookie-parser');
const { check, validationResult } = require('express-validator');

// Initialize Express app
const app = express();
const port = process.env.PORT || 3000;

// Middleware Setup
app.use(helmet()); // Secure HTTP headers
app.use(compression()); // Compress response bodies
app.use(morgan('combined')); // HTTP request logging
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(cookieParser()); // Parse Cookie header

// Set EJS as the templating engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// CSRF Protection Setup
const csrfProtection = csrf({ cookie: true });

// Configure Multer Storage with File Type and Size Validation
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/'); // Ensure this directory exists and is secure
  },
  filename: (req, file, cb) => {
    // Generate a unique filename to prevent collisions
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
    cb(null, 'template-' + uniqueSuffix + path.extname(file.originalname));
  },
});

// Initialize Multer with Storage Configuration
const upload = multer({
  storage: storage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 5 MB file size limit
  fileFilter: (req, file, cb) => {
    // Accept only PDF files
    if (file.mimetype === 'application/pdf') {
      cb(null, true);
    } else {
      cb(new Error('Only PDF files are allowed!'), false);
    }
  },
});

// Serve Static Files (if any)
app.use(express.static('public'));

// Route: Render the HTML Form with CSRF Token
app.get('/', csrfProtection, (req, res) => {
  res.render('form', { csrfToken: req.csrfToken() });
});

// Field Mapping: Map Form Inputs to PDF Field Names
const fieldMappings = {
  attorneyName: 'cname1',      // Attorney Name
  caseNumber: 'ccase',         // Case Number
  petitioner: 'cpet1',         // Petitioner Name
  respondent: 'cresp1',        // Respondent Name
  courtName: 'courtNameField', // Court Name
  hearingDate: 'hearingDateField', // Hearing Date
  hearingTime: 'hearingTimeField', // Hearing Time
  department: 'departmentField',   // Department
  room: 'roomField',               // Room
  // Add more mappings as needed
};

// Route: Handle Form Submission and PDF Processing
app.post(
  '/submit',
  upload.single('pdfTemplate'),
  csrfProtection,
  [
    // Input Validation and Sanitization
    check('attorneyName').trim().escape().notEmpty().withMessage('Attorney Name is required.'),
    check('caseNumber').trim().escape().notEmpty().withMessage('Case Number is required.'),
    check('petitioner').trim().escape().notEmpty().withMessage('Petitioner Name is required.'),
    check('respondent').trim().escape().notEmpty().withMessage('Respondent Name is required.'),
    check('courtName').trim().escape().notEmpty().withMessage('Court Name is required.'),
    check('hearingDate')
      .isISO8601()
      .withMessage('Hearing Date must be a valid date.')
      .toDate(),
    check('hearingTime')
      .matches(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/)
      .withMessage('Hearing Time must be a valid time (HH:MM).'),
    check('department').trim().escape().notEmpty().withMessage('Department is required.'),
    check('room').trim().escape().notEmpty().withMessage('Room is required.'),
    // Add more validations as needed
  ],
  async (req, res) => {
    // Handle Validation Errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      // Delete the uploaded file if validation fails
      if (req.file && req.file.path) {
        fs.unlink(req.file.path, (err) => {
          if (err) console.error('Error deleting the uploaded PDF:', err);
        });
      }
      return res.status(400).render('form', {
        csrfToken: req.csrfToken(),
        errors: errors.array(),
        // Pass previous input values to repopulate the form
        formData: req.body,
      });
    }

    try {
      const pdfPath = req.file.path;
      const existingPdfBytes = fs.readFileSync(pdfPath);

      // Load the PDF Document
      const pdfDoc = await PDFDocument.load(existingPdfBytes, { ignoreEncryption: true });
      const form = pdfDoc.getForm();

      // Populate the PDF Fields Based on Field Mappings
      for (const [formField, pdfField] of Object.entries(fieldMappings)) {
        let value = req.body[formField];

        // Special Formatting for Certain Fields
        if (formField === 'hearingDate') {
          const date = new Date(value);
          // Format: MM/DD/YYYY
          value = `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
        }

        // Attempt to Set the Field in the PDF
        try {
          const field = form.getField(pdfField);
          if (field) {
            const fieldType = field.constructor.name;

            switch (fieldType) {
              case 'PDFTextField':
                field.setText(value);
                break;
              case 'PDFCheckBox':
                if (value.toLowerCase() === 'on' || value === 'true') {
                  field.check();
                } else {
                  field.uncheck();
                }
                break;
              case 'PDFRadioGroup':
                field.select(value);
                break;
              case 'PDFDropdown':
                field.select(value);
                break;
              // Handle other field types as needed
              default:
                console.warn(`Unhandled field type: ${fieldType} for field ${pdfField}`);
            }
          } else {
            console.warn(`Field ${pdfField} not found in the PDF.`);
          }
        } catch (error) {
          console.warn(`Error setting field ${pdfField}:`, error.message);
        }
      }

      // Flatten the PDF to Prevent Further Editing (Optional)
      form.flatten();

      // Serialize the PDF Document
      const pdfBytes = await pdfDoc.save();

      // Define Output Path for the Filled PDF
      const outputPath = path.join(__dirname, `uploads/Filled_FL300_${Date.now()}.pdf`);
      fs.writeFileSync(outputPath, pdfBytes);

      // Send the Filled PDF to the User for Download
      res.download(outputPath, 'Filled_FL300.pdf', (err) => {
        if (err) {
          console.error('Error sending the file:', err);
          res.status(500).send('Error sending the filled PDF.');
        }

        // Cleanup: Delete Both the Uploaded Template and the Filled PDF
        fs.unlink(pdfPath, (err) => {
          if (err) console.error('Error deleting the uploaded PDF:', err);
        });
        fs.unlink(outputPath, (err) => {
          if (err) console.error('Error deleting the filled PDF:', err);
        });
      });
    } catch (error) {
      console.error('Error processing the PDF:', error);

      // Delete the Uploaded File in Case of Error
      if (req.file && req.file.path) {
        fs.unlink(req.file.path, (err) => {
          if (err) console.error('Error deleting the uploaded PDF:', err);
        });
      }

      res.status(500).send('An unexpected error occurred while processing your request.');
    }
  }
);

// Start the Server
app.listen(port, () => {
  console.log(`App running on http://localhost:${port}`);
});
