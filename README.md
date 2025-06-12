# Bot de Afiliados 💼🤖

Este es un bot de Telegram diseñado para gestionar afiliados, ventas de licencias, recargas y control administrativo.

## Funcionalidades principales

- Ver productos y precios
- Recargar saldo con comprobante o sin él
- Solicitar licencias (una por usuario, no repetidas)
- Panel de administración:
  - Gestión de afiliados
  - Control de stock
  - Aprobación y rechazo de recargas
  - Edición de productos
  - Historial y reversión de rechazos

## Requisitos

- Python 3.10+
- Librerías especificadas en `requirements.txt`

## Variables de entorno

En Render o local puedes usar:

```
BOT_TOKEN=tu_token_aqui
```

## Cómo correr localmente

```bash
pip install -r requirements.txt
python main.py
```
