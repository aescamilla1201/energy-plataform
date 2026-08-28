# Tuya Energy API

Consultar sensores eléctricos conectados a Tuya Cloud

##Objetivo inicial 

- Obtener un access token de Tuya.
- Consultar los detalles de un dispositivo.
- Consultar su estado actual.
- Identificar los Data Points eléctricos.
- Normalizar las mediciones.

Flujo de monitor_sensor.py
                    ┌──────────────────┐
                    │ Cargar settings  │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Cargar sensores  │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Filtrar enabled  │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Conectar a Tuya  │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Consultar sensor │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Extraer datos    │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Normalizar datos │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Guardar en CSV   │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Esperar 10 min   │
                    └────────┬─────────┘
                             │
                             └──────→ repetir