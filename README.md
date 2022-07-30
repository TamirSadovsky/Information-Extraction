
# :information_source: Information-Extraction 

In this project, information extraction technology is applied to answering natural language questions about geography with ontologies, Xpath, SPARQL, and HTML.


The information for the ontology collected from:
https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)
## :arrow_right: Deployment

To create the ontology run:

```python geo_qa.py create```
  
To ask a question run:

```python geo_qa.py question “<question>”```
  
Upon receiving a natural language question, the question translated into a SPARQL query that runs over the constructed ontology.  
The answer to the question is printed and the program terminates.


## :framed_picture:	Screenshots

![Project Screenshot](file:///D:/Downloads/Infromation_extraction_sc1.jpg?raw=true "Optional Title")


## :man_technologist:	Authors

- [@TamirSadovsky](https://github.com/TamirSadovsky)
- [@LiriNorkin](https://github.com/LiriNorkin)
