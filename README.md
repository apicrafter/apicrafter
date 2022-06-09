# APICrafter
API wrapper for MongoDB databases

APICrafter creates Python Eve wrapper over MongoDB database/databases, creates Eve scheme for each collection and generates OpenAPI (Swagger) documentation.

# Commands

## Discover

Creates apicrafter.yml API description file from database or collection. Automatically generates data schemas from original data

Build API definition as apicrafter.yml
```apicrafter discover -h 127.0.0.1 -p 27017 -d rusregions```

## Run

Uses API definition from apicrafter.yml file and launches API server over MongoDB.
You could 

Run server
```apicrafter run```


# Examples

Please see /examples directory for data and usage


