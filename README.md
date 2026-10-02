### 1. Ejecución con Interfaz Gráfica
```bash
python app.py
```

### 2. Modo Consola (Terminal)
```bash
python automatas/main.py
```

---

## Requisitos

- **Python 3.8 o superior**
- **Librería graphviz para Python**:
  ```bash
  pip install graphviz
  ```
- **Graphviz instalado en el sistema**:
  - En Windows: Descargar desde [graphviz.org/download](https://graphviz.org/download/) y asegurarse de marcar la opción *"Add Graphviz to system PATH"*.
  - En Linux: `sudo apt-get install graphviz`

---

## Expresiones Regulares Soportadas

| Operador   | Significado           | Ejemplo     |
|----------  |-----------------------|-------------|
| `\|`       | Unión (o)             | `a\|b`      |
|(implícito) | Concatenación         | `ab`        |
| `*`        | Cero o más veces      | `a*`        |
| `+`        | Una o más vece        | `a+`        |
| `( )`      | Agrupación            |`(a\|b)*c`   |
