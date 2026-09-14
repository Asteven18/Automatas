## Requisitos

- Python
- Graphviz instalado en el sistema:
Windows: instalar desde https://graphviz.org/download/ y agregarlo al PATH (Add Graphviz to the system PATH)
pip install graphviz

```
## Ejecución
python main.py
```

## Sintaxis de expresiones regulares soportada

| Operador   | Significado           | Ejemplo     |
|----------  |-----------------------|-------------|
| `\|`       | Unión (o)             | `a\|b`      |
|(implícito) | Concatenación         | `ab`        |
| `*`        | Cero o más veces      | `a*`        |
| `+`        | Una o más vece        | `a+`        |
| `?`        | Cero o una vez        | `a?`        |
| `( )`      | Agrupación            |`(a\|b)*c`   |
