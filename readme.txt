ClubOS

> Sistema de gestión inteligente y equitativa para clubes y capítulos universitarios, impulsado por Google Gemma.

---

¿Qué problema resolvemos?
En las comunidades y clubes universitarios, es muy común el fenómeno del burnout (agotamiento) en las juntas directivas, donde los miembros antiguos cargan con todo el trabajo mientras que los nuevos integrantes se quedan al margen por falta de asignación clara de roles. 
 
ClubOS automatiza la organización del club extrayendo tareas, eventos y sugerencias directamente desde los historiales de chat de WhatsApp y afiches mediante Inteligencia Artificial, distribuyendo las cargas de trabajo de manera justa según la jerarquía de los miembros.

---

Características Principales
-Extracción Inteligente con Gemma:Analiza historiales de chat (`.txt`) y flyers en imagen en una sola llamada multimodal utilizando la API de Gemini.
- Distribución Equitativa (Anti-Burnout): Asigna tareas automáticamente al miembro con menor carga actual basándose en un sistema de pesos por jerarquía (Admin, Miembro, Novato).
- Detección de Eventos y Alertas: Identifica fechas, horas y detalles clave de futuros eventos del club.
- Buzón Automatizado: Recopila quejas, sugerencias y propuestas mencionadas en las conversaciones.

---

Tecnologías Utilizadas
- Backend:Python, FastAPI, SQLAlchemy, Uvicorn.
- Inteligencia Artificial: Google Gemma (`gemma-4-31b-it`) vía `google-genai` SDK.
- Frontend: HTML5, Tailwind CSS, JavaScript (Jinja2 Templates).
- Base de Datos: SQLite / SQLAlchemy.
