---

# Semantic Data Search

This repository contains an Search, designed to run a local web service for asking questions, querying, and managing academic resources using weaviate vector db. Follow the instructions below to get started with setup, running the application, and using the API.

## Setup

### Install Python Packages

To install the required Python packages, use the following command:

```bash
pip install -r requirements.txt
```

If the above command does not work, install the required packages individually using pip.

### Install Project Locally

To ensure the imports from this project work correctly, navigate to the `sch-search` directory and run:

```bash
cd sch-search
pip install -e .
```

## Running the Application

To start the application, run:

```bash
python index.py
```

The app will run locally at `localhost:3000`.

## API Documentation

### Important: API Password Requirement

For all API calls, you **MUST INCLUDE** an api key from Weaviate: https://weaviate.io/developers/wcs/connect

---

### Add Resources

**Endpoint:** `POST /add_resources`

Example request:

```json
{
  "links": [
    "https://faculty.econ.ucdavis.edu/faculty/bonanno/PDF/GT_book.pdf"
  ],
  "password": "see /weaviate/weaviate_calls_dev.py for PASSWORD variable"
}
```

Example response:

```json
{
  "links added": [
    "https://faculty.econ.ucdavis.edu/faculty/bonanno/PDF/GT_book.pdf"
  ],
  "error": "None"
}
```

Example response (missing password):

```json
{
  "links added": [],
  "error": "MUST INCLUDE PASSWORD IN JSON REQUEST BODY"
}
```

Example response (invalid password):

```json
{
  "links added": [],
  "error": "INVALID PASSWORD"
}
```

---

### Delete Resources

**Endpoint:** `DELETE /del_resources`

Example request:

```json
{
  "links": [
    "https://faculty.econ.ucdavis.edu/faculty/bonanno/PDF/GT_book.pdf"
  ]
}
```

Example response:

```json
{
  "output": {
    "result": [
      "Item removed: https://faculty.econ.ucdavis.edu/faculty/bonanno/PDF/GT_book.pdf"
    ]
  },
  "error": ""
}
```

---

### Query Weaviate - Question and Answer Instance

**Endpoint:** `GET /query_qa`

Example request:

```json
{
  "query": "What is the term for a strategy that yields a higher payoff regardless of the opponent's choice?",
  "limit": 2
}
```

Example response:

```json
[
  {
    "content": "Dominant strategy.",
    "document": "https://faculty.econ.ucdavis.edu/faculty/bonanno/PDF/GT_book.pdf",
    "page": "12",
    "paragraph": "2"
  },
  {
    "content": "Nash equilibrium.",
    "document": "https://faculty.econ.ucdavis.edu/faculty/bonanno/PDF/GT_book.pdf",
    "page": "14",
    "paragraph": "4"
  }
]
```

---

### Query Weaviate - Basic Instance

**Endpoint:** `GET /query_basic`

Example request:

```json
{
  "query": "solution concept players choosing strategies",
  "limit": 1
}
```

Example response:

```json
[
  {
    "content": "Nash equilibrium.",
    "document": "https://faculty.econ.ucdavis.edu/faculty/bonanno/PDF/GT_book.pdf",
    "page": "14",
    "paragraph": "4"
  }
]
```

---

## Additional Files

This repository also includes Python scripts for parsing videos, CSV files, and PDFs, as well as making Weaviate calls for resource management. These include:

- `video_parser.py`: Script for video data parsing.
- `csv_parser.py`: Script for parsing CSV files.
- `pdf_parser.py`: Script for PDF file parsing.
- `weaviate_calls.py`: Functions for interacting with Weaviate.
- `weaviate_calls_dev.py`: Development version for testing Weaviate calls.
- `add_resource.py`: Functions for adding resources.
- `del_resource.py`: Functions for deleting resources.
- `query.py`: Script for querying data.
