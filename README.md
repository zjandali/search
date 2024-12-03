
---

# Academic Search

This repository contains the a Search project, designed to run a local web service for querying and managing academic resources. Follow the instructions below to get started with setup, running the application, and using the API.

## Setup

### Install Python Packages

To install the required Python packages, use the following command:

```bash
pip install -r requirements.txt
```

If the above command does not work, install the required packages individually using pip.

### Install Project Locally

To ensure the imports from this project work correctly, navigate to the `scholarhub-search` directory and run:

```bash
cd scholarhub-search
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

For all API calls, you **MUST INCLUDE** a password field in the JSON request body. You can find the required password in the `sch_search/weaviate/weaviate_calls_dev.py` file under the variable `PASSWORD`.

---

### Add Resources

**Endpoint:** `POST /add_resources`

Example request:

```json
{
  "links": [
    "https://www.eecs70.org/static/notes/n1.pdf",
    "https://www.eecs70.org/static/notes/n2.pdf"
  ],
  "password": "see sch_search/weaviate/weaviate_calls_dev.py for PASSWORD variable"
}
```

Example response:

```json
{
  "links added": [
    "https://www.eecs70.org/static/notes/n1.pdf",
    "https://www.eecs70.org/static/notes/n2.pdf"
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
    "https://www.eecs70.org/static/notes/n1.pdf"
  ]
}
```

Example response:

```json
{
  "output": {
    "result": [
      "Item removed: https://www.eecs70.org/static/notes/n1.pdf"
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
  "query": "What is the definition of a planar graph?",
  "limit": 2
}
```

Example response:

```json
[
  {
    "content": "Can you see why planar graphs generalize polyhedra? Why are all polyhedra (without holes) planar graphs?",
    "document": "https://www.sp18.eecs70.org/static/notes/n5.pdf",
    "page": "7",
    "paragraph": "3"
  },
  {
    "content": "When a planar graph is drawn on the plane, one can distinguish vertices, edges, and faces...",
    "document": "https://www.sp18.eecs70.org/static/notes/n5.pdf",
    "page": "7",
    "paragraph": "1"
  }
]
```

---

### Query Weaviate - Basic Instance

**Endpoint:** `GET /query_basic`

Example request:

```json
{
  "query": "law about negation",
  "limit": 1
}
```

Example response:

```json
[
  {
    "content": "By the above laws, we can do it as follows: ¬(∃x∃yP(x, y)) ? ∃x¬(∃yP(x, y))...",
    "document": "https://www.sp18.eecs70.org/static/notes/n1.pdf",
    "page": "6",
    "paragraph": "1"
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


