# setup

### python packages
use pip (pip3)

`pip install -r requirements.txt`
if this does not work, install these packages and others as needed with pip commands

To install search so that the imports from this project work:
```
cd scholarhub-search
pip install -e .
````

# run
```
python index.py
- app runs locally at localhost:3000
```
## API
```
for API calls, you MUST INCLUDE PASSWORD FIELD in json request body:
see sch_search/weaviate/weaviate_calls_dev.py for PASSWORD variable
```
### add resources
POST /add_resources
example request:
```
{
  "links": [
      "https://www.eecs70.org/static/notes/n1.pdf",
      "https://www.eecs70.org/static/notes/n2.pdf"
  ],
  "password":  "see sch_search/weaviate/weaviate_calls_dev.py for PASSWORD variable"
}
```
```
{
  "links": [
    "https://www.youtube.com/watch?v=LDJyhXGBmEM&ab_channel=MeganMcCarter"
  ]
  "password": "see sch_search/weaviate/weaviate_calls_dev.py for PASSWORD variable"
}
```
example Response:
```
{
    "links added": [
    "https://www.eecs70.org/static/notes/n1.pdf",
    "https://www.eecs70.org/static/notes/n2.pdf"
    ]

    },
    "error": "None"
}
```
```
{
    "links added": [
    "https://www.youtube.com/watch?v=LDJyhXGBmEM&ab_channel=MeganMcCarter"
    ]

    },
    "error": "None"
}
```
example response with no password:

```
{
  "links added": [],
  "error": "MUST INCLUDE PASSWORD IN JSON REQUEST BODY"
}
```
example response with invalid password:
```
{
    "links added" = [],
    "error": "INVALID PASSWORD"
}
```
example response (already added resource):
```
{
    "links added" = []
    "error": "FILE ALREADY ADDED"
}
```
### delete resources
DELETE /del_resources

example request:
```
{
  "links": [
    "https://www.eecs70.org/static/notes/n1.pdf"
  ]
}
```
example response:
```
{
    "output": {
        "result": [
            "Item removed: https://www.eecs70.org/static/notes/n1.pdf"
        ]
    },
    "error": ""
}
```
### query weaviate

##### query weaviate question and answer instance:
GET /query_qa

example query:
```
{
  "query": "What is the definition of a planar graph?",
  "limit": 2
}
```
example response:
```
[
    {
        "content": "Can you see why planar graphs generalize polyhedra? Why are all polyhedra (without �holes�) planar graphs?",
        "document": "https://www.sp18.eecs70.org/static/notes/n5.pdf",
        "page": "7",
        "paragraph": "3"
    },
    {
        "content": "When a planar graph is drawn on the plane, one can distinguish, besides its vertices (their number will be denoted v here) and edges (their number is e), the faces of the graph (more precisely, of the drawing). The faces are the regions into which the graph subdivides the plane. One of them is infinite, and the others are finite. The number of faces is denoted f . For example, for the first graph shown f = 4, and for the fourth (the cube) f = 6.",
        "document": "https://www.sp18.eecs70.org/static/notes/n5.pdf",
        "page": "7",
        "paragraph": "1"
    }
]
```
##### query weaviate basic instance:
GET /query_basic

example query:
```
{
    "query": "law about negation",
    "limit": 1
}
```
example response:
```
[
    {
        "content": "To see a more complex example, fix some universe and propositional formula P(x, y). Assume we have the proposition �(?x?yP(x, y)) and we want to push the negation operator inside the quantifiers. By the above laws, we can do it as follows: �(?x?yP(x, y)) ? ?x�(?yP(x, y)) ? ?x?y�P(x, y). Notice that we broke the complex negation into a smaller, easier problem as the negation propagated itself through the quantifiers. Note also that the quantifiers �flip� as we go.",
        "document": "https://www.sp18.eecs70.org/static/notes/n1.pdf",
        "page": "6",
        "paragraph": "1"
    }
]
```
