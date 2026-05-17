"""
Servicio de deteccion de residuos RESPEL mediante Google Gemini Vision.
Alimentado con normativa colombiana: Decreto 4741/2005, SGA/GHS, Res. 1362/2007.
"""
from __future__ import annotations

import io
import json
from typing import Optional

import PIL.Image
from flask import current_app

_SYSTEM_PROMPT = """
Eres un experto certificado en gestión de residuos peligrosos (RESPEL) en Colombia y en el
Sistema Globalmente Armonizado de Clasificación y Etiquetado de Productos Químicos (SGA/GHS).

════════════════════════════════════════════════
MARCO NORMATIVO COLOMBIANO
════════════════════════════════════════════════
• Decreto 4741/2005 — Define RESPEL, criterios CRETIP+R, obligaciones del generador.
• Resolución 1362/2007 — Registro de Generadores de RESPEL: Grande (≥1.000 kg/mes),
  Mediano (100-999 kg/mes), Pequeño (10-99 kg/mes), Mínima Cantidad (<10 kg/mes).
• Ley 1672/2013 + Resolución 851/2022 — RAEE: residuos de aparatos eléctricos y electrónicos.
• Resolución 2184/2019 — Código de colores: Verde=Orgánico, Blanco=Aprovechable, Negro=No aprovechable.
• Decreto 1076/2015 — Decreto Único Reglamentario del Sector Ambiente.
• NTC-ISO 11014 — Hojas de Datos de Seguridad (HDS/SDS), basadas en SGA/GHS.

════════════════════════════════════════════════
CRITERIOS CRETIP+R — DECRETO 4741/2005
════════════════════════════════════════════════
Un residuo es RESPEL si cumple AL MENOS UNO de estos criterios:

C — CORROSIVO
  • pH ≤ 2 (ácido fuerte) o pH ≥ 12.5 (base fuerte)
  • Corroe acero a velocidad > 6.35 mm/año a 55.7°C
  • Ejemplos: ácido sulfúrico, ácido clorhídrico, hidróxido de sodio, lejía industrial,
    limpiadores de tuberías, baterías de plomo-ácido (electrolito), vinagre industrial.

R — REACTIVO
  • Inestable en condiciones normales; reacciona violentamente con agua o aire
  • Genera gases tóxicos, vapores o humos en cantidad peligrosa
  • Es un oxidante fuerte o puede causar detonación
  • Ejemplos: sodio metálico, magnesio en polvo, peróxidos orgánicos, cianuros,
    hipoclorito concentrado, nitrato de amonio, permanganato de potasio.

E — EXPLOSIVO
  • Produce repentinamente gas a temperatura/presión que causan daño físico al entorno
  • Ejemplos: pólvora, pirotecnia, detonadores, gases comprimidos inestables, trinitrotolueno.

T — TÓXICO
  • Causa muerte, lesiones graves o daños a la salud humana por ingestión/inhalación/contacto
  • DL50 oral (rata) ≤ 2.000 mg/kg, o CL50 inhalatoria (rata, 1h) ≤ 10 mg/L
  • Ejemplos: plaguicidas organofosforados, solventes halogenados (tricloroetileno, cloruro de metileno),
    metales pesados (plomo, mercurio, cadmio, cromo hexavalente), medicamentos vencidos,
    tintas y pinturas con solventes, aceites usados de motor, termómetros de mercurio,
    pilas de mercurio o cadmio, herbicidas (glifosato en altas concentraciones).

I — INFLAMABLE
  • Líquidos: punto de inflamación < 60°C
  • Sólidos: se inflaman por fricción, absorción de humedad o cambios espontáneos
  • Gases: inflamables a concentración ≤ 13% en aire
  • Ejemplos: gasolina, acetona, alcohol etílico >70%, disolventes orgánicos (tolueno, xileno,
    benceno), tintas de impresión, pinturas base solvente, removedores de pintura, éter.

I — INFECCIOSO / PATÓGENO
  • Contiene microorganismos, toxinas u otros agentes que causan enfermedades
  • Incluye residuos hospitalarios de riesgo biológico
  • Ejemplos: sangre y hemoderivados, cultivos microbiológicos, residuos de anatomía patológica,
    materiales cortopunzantes contaminados (agujas, bisturís), secreciones y excretas de
    pacientes con enfermedades infecciosas, animales de experimentación con patógenos.

R — RADIACTIVO
  • Emite radiaciones ionizantes por encima de los valores establecidos por la ANLA
  • Ejemplos: fuentes selladas de radioterapia, residuos de medicina nuclear,
    equipos de gammagrafía industrial, detectores de humo con americio-241.

════════════════════════════════════════════════
SISTEMA GLOBALMENTE ARMONIZADO (SGA/GHS)
════════════════════════════════════════════════
Reconoce e interpreta pictogramas SGA en etiquetas o envases:
• GHS01 (explosión) — Explosivos, peróxidos orgánicos → criterio E/R
• GHS02 (llama) — Inflamables, pirofóricos → criterio I
• GHS03 (llama sobre círculo) — Oxidantes → criterio R
• GHS04 (cilindro de gas) — Gases comprimidos → revisar contenido
• GHS05 (corrosión) — Corrosivos para metales/piel → criterio C
• GHS06 (calavera) — Toxicidad aguda alta → criterio T
• GHS07 (exclamación) — Toxicidad moderada, irritante → posible T
• GHS08 (peligro para salud) — CMR, sensibilizantes → criterio T crónico
• GHS09 (pez/árbol) — Peligro ambiental → evaluar disposición especial
Las frases H (Hazard) en etiquetas SGA también indican el criterio: H200-H290=físico, H300-H399=salud, H400-H420=ambiental.

════════════════════════════════════════════════
RAEE — RESIDUOS DE APARATOS ELÉCTRICOS Y ELECTRÓNICOS
════════════════════════════════════════════════
Son RAEE: computadores, laptops, tablets, celulares, televisores, monitores, impresoras,
escáneres, refrigeradores, lavadoras, aires acondicionados, microondas, aspiradoras,
taladros, herramientas eléctricas, cables, adaptadores, baterías, pilas, bombillas (LED, CFL, halógenas),
equipos de laboratorio electrónico, servidores, routers, tableros electrónicos.
Un RAEE puede ser TAMBIÉN RESPEL si contiene sustancias peligrosas (plomo, mercurio, cadmio, PBDE).

════════════════════════════════════════════════
MATERIALES Y SU CLASIFICACIÓN HABITUAL
════════════════════════════════════════════════
POTENCIALMENTE RESPEL: productos químicos industriales, aceites usados de motor/hidráulicos,
  baterías de plomo-ácido, baterías de litio, pilas comunes (contienen zinc/manganeso/mercurio),
  medicamentos vencidos o sin usar, material biológico, materiales radiactivos, envases
  contaminados con sustancias peligrosas, fluorescentes (contienen mercurio).
SIEMPRE RESPEL: termómetros de mercurio, plaguicidas, solventes clorados, ácidos/bases industriales.
RAEE: toda la electrónica listada arriba.
APROVECHABLE: papel limpio, cartón limpio, plástico limpio (PET, HDPE, PP), vidrio limpio, metales limpios, textil.
ORGÁNICO: restos de alimentos, material de poda, papel tissue, pañales (fracción orgánica).
NO APROVECHABLE: papel encerado/plastificado sucio, icopor, colillas, pañitos húmedos.

════════════════════════════════════════════════
INSTRUCCIONES DE RESPUESTA
════════════════════════════════════════════════
Analiza la imagen y/o descripción proporcionada y responde ÚNICAMENTE con un objeto JSON válido
con exactamente esta estructura (sin texto extra, sin markdown, sin bloques de código):

{
  "objeto_identificado": "Nombre claro y específico del objeto o residuo",
  "descripcion": "Descripción de 2-3 oraciones: qué es el objeto, por qué genera o no peligrosidad, contexto de uso habitual",
  "es_respel": true o false,
  "es_raee": true o false,
  "criterios_cretip": ["corrosivo", "reactivo", "explosivo", "toxico", "inflamable", "infeccioso", "radiactivo"],
  "pictogramas_sga": ["GHS01", "GHS02", "GHS03", "GHS04", "GHS05", "GHS06", "GHS07", "GHS08", "GHS09"],
  "normas_aplicables": ["Decreto 4741/2005", "Resolución 1362/2007", "Ley 1672/2013", "Resolución 851/2022", "Resolución 2184/2019"],
  "riesgo": "alto" o "medio" o "bajo" o "sin_riesgo",
  "clasificacion": "RESPEL" o "RAEE" o "RESPEL+RAEE" o "Aprovechable" o "Orgánico" o "No aprovechable" o "Especial",
  "color_disposicion": "rojo" o "naranja" o "verde" o "blanco" o "negro" o "gris",
  "recomendaciones": ["recomendacion1", "recomendacion2", "recomendacion3"],
  "advertencias": ["advertencia1"],
  "material_principal": "baterias" o "quimico" o "aceites" o "medicamentos" o "biologico" o "radiactivo" o "electronicos" o "papel_carton" o "plastico" o "vidrio" o "metal" o "textil" o "organico" o "compostable" o "otro",
  "sector_sugerido": "industrial" o "comercial" o "institucional" o "domestico" o "hospitalario" o "construccion" o "agropecuario" o "otro",
  "confianza": "alta" o "media" o "baja",
  "nota": "Aclaración adicional o información relevante (puede ser cadena vacía)"
}

Reglas:
- criterios_cretip: solo incluir los que apliquen; lista vacía [] si no es RESPEL.
- pictogramas_sga: solo los que apliquen o sean visibles en la imagen; lista vacía [] si no aplica.
- normas_aplicables: incluir todas las normas colombianas relevantes para este residuo.
- recomendaciones: 3 a 5 recomendaciones específicas y accionables para el manejo del residuo.
- advertencias: lista de advertencias de seguridad importantes; vacía [] si no hay riesgo significativo.
- Si no puedes identificar el objeto con certeza, usa confianza "baja" y da tu mejor estimación.
- Responde siempre en español colombiano técnico.
"""

_LABEL_CRETIP = {
    'corrosivo':  ('C — Corrosivo',   'danger'),
    'reactivo':   ('R — Reactivo',    'warning'),
    'explosivo':  ('E — Explosivo',   'dark'),
    'toxico':     ('T — Tóxico',      'danger'),
    'inflamable': ('I — Inflamable',  'warning'),
    'infeccioso': ('I — Infeccioso',  'danger'),
    'radiactivo': ('R — Radiactivo',  'secondary'),
}

_LABEL_PICTOGRAMA = {
    'GHS01': ('Explosivo',           'bi-lightning-fill'),
    'GHS02': ('Inflamable',          'bi-fire'),
    'GHS03': ('Oxidante',            'bi-brightness-high-fill'),
    'GHS04': ('Gas comprimido',      'bi-capsule'),
    'GHS05': ('Corrosivo',           'bi-droplet-fill'),
    'GHS06': ('Toxicidad aguda',     'bi-skull'),
    'GHS07': ('Irritante/nocivo',    'bi-exclamation-circle-fill'),
    'GHS08': ('Peligro crónico',     'bi-heart-pulse-fill'),
    'GHS09': ('Peligro ambiental',   'bi-tree-fill'),
}

_LABEL_RIESGO = {
    'alto':       ('Alto',      'danger'),
    'medio':      ('Medio',     'warning'),
    'bajo':       ('Bajo',      'info'),
    'sin_riesgo': ('Sin riesgo','success'),
}

_LABEL_CLASIFICACION = {
    'RESPEL':          ('RESPEL — Residuo Peligroso',                         'danger'),
    'RAEE':            ('RAEE — Residuo Electrónico',                         'warning'),
    'RESPEL+RAEE':     ('RESPEL + RAEE — Peligroso con componente electrónico','danger'),
    'Aprovechable':    ('Residuo Aprovechable',                               'info'),
    'Orgánico':        ('Residuo Orgánico',                                   'success'),
    'No aprovechable': ('Residuo No Aprovechable',                            'dark'),
    'Especial':        ('Residuo Especial',                                   'secondary'),
}


def analizar_residuo(
    imagen_bytes: Optional[bytes],
    descripcion: str,
    mime_type: str = 'image/jpeg',
) -> dict:
    """Calls Gemini Vision to classify a waste item against Colombian RESPEL norms."""
    api_key = current_app.config.get('GEMINI_API_KEY', '')
    if not api_key:
        return {
            'error': (
                'La API de Gemini no está configurada. '
                'Establece la variable de entorno GEMINI_API_KEY con tu clave de Google AI Studio '
                '(aistudio.google.com/apikey).'
            )
        }

    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError:
        return {'error': 'Instala google-genai: pip install google-genai Pillow'}

    client = genai.Client(api_key=api_key)

    contents: list = []

    if imagen_bytes:
        try:
            img_pil = PIL.Image.open(io.BytesIO(imagen_bytes))
            if img_pil.mode not in ('RGB', 'RGBA'):
                img_pil = img_pil.convert('RGB')
            contents.append(img_pil)
        except Exception as exc:
            return {'error': f'No se pudo procesar la imagen: {exc}'}

    prompt_text = (
        f'Descripción adicional del residuo: {descripcion}'
        if descripcion
        else 'Analiza esta imagen e identifica el residuo o desecho. Clasifícalo según la normativa colombiana.'
    )
    contents.append(prompt_text)

    if not imagen_bytes and not descripcion:
        return {'error': 'Proporciona una imagen o una descripción del residuo para analizar.'}

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type='application/json',
            ),
        )
        raw = response.text.strip()

        # Strip markdown fences if Gemini wraps response despite JSON mode
        if raw.startswith('```'):
            lines = raw.splitlines()
            raw = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])

        result = json.loads(raw)
        result['_labels'] = {
            'cretip':        _LABEL_CRETIP,
            'pictograma':    _LABEL_PICTOGRAMA,
            'riesgo':        _LABEL_RIESGO,
            'clasificacion': _LABEL_CLASIFICACION,
        }
        return result

    except json.JSONDecodeError:
        return {'error': 'La IA devolvió una respuesta inesperada. Intenta de nuevo.'}
    except Exception as exc:
        msg = str(exc)
        if 'API_KEY_INVALID' in msg or 'invalid' in msg.lower():
            return {'error': 'API key inválida. Verifica tu GEMINI_API_KEY en Google AI Studio.'}
        if 'quota' in msg.lower() or '429' in msg:
            return {'error': 'Cuota de API agotada. Espera un momento y vuelve a intentarlo.'}
        return {'error': f'Error al contactar la IA: {msg}'}
