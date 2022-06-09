# Russian regions database example


Restore database
```mongorestore```

Build API definition as apicrafter.yml
```apicrafter discover -h 127.0.0.1 -p 27017 -d rusregions```



Run server
```apicrafter run```

Access API endpoints

Cities
```curl https://127.0.0.1:10092/v1/rusregions/cities```

Regions
```curl https://127.0.0.1:10092/v1/rusregions/regions```

# Original source

Russian regions metadata https://datacrafter.ru/packages/rusregions
