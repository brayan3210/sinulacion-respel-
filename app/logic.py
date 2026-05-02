"""
Módulo de lógica de clasificación de residuos.

Marco normativo base:
  - Decreto 4741/2005: RESPEL - prevención y manejo
  - Resolución 1362/2007: registro de generadores RESPEL
  - Ley 1672/2013 y Resolución 851/2022: RAEE
  - Decreto 1077/2015 y Resolución 2184/2019: residuos sólidos

AVISO: Esta lógica tiene carácter educativo y orientativo.
No constituye dictamen legal ni sustituye asesoría ambiental especializada.
"""

from __future__ import annotations
from typing import Any

# ---------------------------------------------------------------------------
# Catálogos de materiales por categoría
# ---------------------------------------------------------------------------

MATERIALES_RAEE = {'electronicos', 'componentes_electronicos'}

MATERIALES_POTENCIALMENTE_PELIGROSOS = {
    'quimico', 'aceites', 'baterias', 'medicamentos',
    'biologico', 'radiactivo',
}

MATERIALES_APROVECHABLES = {
    'papel_carton', 'plastico', 'vidrio', 'metal', 'textil',
}

MATERIALES_ORGANICOS = {'organico', 'compostable'}

SECTORES_DISPLAY = {
    'industrial':      'Industrial / Manufacturero',
    'comercial':       'Comercial / Servicios',
    'institucional':   'Institucional / Educativo',
    'domestico':       'Doméstico / Residencial',
    'hospitalario':    'Hospitalario / Salud',
    'construccion':    'Construcción y Demolición',
    'agropecuario':    'Agropecuario / Agrícola',
    'otro':            'Otro / No especificado',
}

ESTADOS_FISICOS_DISPLAY = {
    'solido':      'Sólido',
    'liquido':     'Líquido',
    'lodo':        'Lodo / Semisólido',
    'gas':         'Gas / Vapor',
    'semiliquido': 'Semilíquido / Pastoso',
}

MATERIALES_DISPLAY = {
    'organico':                 'Orgánico / Restos de alimentos',
    'compostable':              'Compostable / Jardín',
    'papel_carton':             'Papel / Cartón',
    'plastico':                 'Plástico',
    'vidrio':                   'Vidrio',
    'metal':                    'Metal / Chatarra',
    'textil':                   'Textil / Telas',
    'quimico':                  'Sustancia o residuo químico',
    'biologico':                'Biológico / Patogénico',
    'radiactivo':               'Radiactivo',
    'electronicos':             'Aparatos eléctricos / electrónicos',
    'componentes_electronicos': 'Componentes electrónicos',
    'aceites':                  'Aceites / Lubricantes',
    'baterias':                 'Baterías / Pilas',
    'medicamentos':             'Medicamentos / Fármacos',
    'especial':                 'Residuo especial (llantas, escombros, etc.)',
    'otro':                     'Otro / No especificado',
}


# ---------------------------------------------------------------------------
# Función principal de clasificación
# ---------------------------------------------------------------------------

def clasificar_residuo(datos: dict[str, Any]) -> dict[str, Any]:
    """
    Clasifica un residuo y devuelve un diccionario con la ruta normativa,
    obligaciones, advertencias y recomendaciones aplicables.
    """
    resultado: dict[str, Any] = {
        'clasificacion':                    '',
        'clasificacion_corta':              '',
        'ruta':                             '',
        'normas_aplicables':                [],
        'peligroso':                        False,
        'raee':                             False,
        'ambiguo':                          False,
        'requiere_evaluacion_peligrosidad': False,
        'categoria_generador':              None,
        'obligaciones':                     [],
        'recomendaciones':                  [],
        'advertencias':                     [],
        'criterios_detectados':             [],
        'nivel_cumplimiento':               '',
        'color_ruta':                       'secondary',
        'badge_color':                      'secondary',
        'icono_ruta':                       'bi-question-circle',
        'descripcion_resultado':            '',
    }

    material           = datos.get('material_principal', '')
    sector             = datos.get('sector_fuente', '')
    proviene_elec      = datos.get('proviene_electronico', False)
    contacto_quimico   = datos.get('contacto_quimico', False)
    mezclado           = datos.get('mezclado', False)
    envase_contaminado = datos.get('envase_contaminado', False)
    criterios          = datos.get('criterios_peligrosidad', {})

    # --- Evaluación de criterios de peligrosidad marcados por el usuario ---
    criterios_activos = [k for k, v in criterios.items() if v]
    es_peligroso = len(criterios_activos) > 0

    # --- Señales que disparan la evaluación de peligrosidad ---
    if material in MATERIALES_POTENCIALMENTE_PELIGROSOS:
        resultado['requiere_evaluacion_peligrosidad'] = True
        resultado['advertencias'].append(
            f'El tipo de material seleccionado ({MATERIALES_DISPLAY.get(material, material)}) '
            'puede presentar características de peligrosidad. Se recomienda verificar '
            'criterios CRETIP+R según el Decreto 4741 de 2005 (Art. 6).'
        )

    if sector == 'hospitalario':
        resultado['requiere_evaluacion_peligrosidad'] = True
        resultado['advertencias'].append(
            'Los residuos del sector hospitalario o de salud pueden ser infecciosos. '
            'Considere también el Decreto 351 de 2014 (Residuos Hospitalarios y Similares).'
        )

    if contacto_quimico:
        resultado['requiere_evaluacion_peligrosidad'] = True
        resultado['advertencias'].append(
            'El contacto previo con sustancias químicas o biológicas puede conferir '
            'características de peligrosidad al residuo. Evalúe criterios de peligrosidad.'
        )

    if envase_contaminado:
        es_peligroso = True
        resultado['advertencias'].append(
            'Los envases, empaques o embalajes que hayan estado en contacto con sustancias '
            'peligrosas deben manejarse como RESPEL. '
            '(Artículo 10, numeral 1, Decreto 4741 de 2005)'
        )
        resultado['criterios_detectados'].append('Envase / empaque contaminado con sustancia peligrosa')

    if mezclado:
        resultado['advertencias'].append(
            'La mezcla de residuos peligrosos con no peligrosos puede incrementar '
            'el volumen de RESPEL a gestionar y eleva los costos. '
            'Implemente separación en la fuente de forma inmediata.'
        )

    resultado['criterios_detectados'].extend(criterios_activos)

    # --- Determinar si es RAEE ---
    es_raee = proviene_elec or (material in MATERIALES_RAEE)
    if es_raee:
        resultado['raee'] = True

    # --- Árbol de decisión normativo ---
    if es_peligroso and es_raee:
        _set_resultado_respel_raee(resultado)

    elif es_peligroso:
        _set_resultado_respel(resultado)

    elif es_raee:
        _set_resultado_raee(resultado)

    elif resultado['requiere_evaluacion_peligrosidad'] and not criterios:
        # Material potencialmente peligroso pero aún no se evaluaron criterios
        _set_resultado_ambiguo(resultado)

    else:
        # Residuo no peligroso — clasificar según Resolución 2184/2019
        _set_resultado_no_peligroso(resultado, material)

    # --- Categoría del generador (aplica solo a RESPEL) ---
    if resultado['peligroso']:
        resultado['categoria_generador'] = _determinar_categoria_generador(datos)

    # --- Obligaciones del generador ---
    if resultado['peligroso']:
        resultado['obligaciones'] = get_obligaciones_respel(
            resultado.get('categoria_generador', '')
        )

    # --- Nivel de cumplimiento estimado ---
    resultado['nivel_cumplimiento'] = _estimar_nivel_cumplimiento(resultado, datos)

    # --- Recomendaciones ---
    resultado['recomendaciones'] = get_recomendaciones(resultado, datos)

    return resultado


# ---------------------------------------------------------------------------
# Setters internos por tipo de clasificación
# ---------------------------------------------------------------------------

def _set_resultado_respel_raee(r: dict) -> None:
    r['clasificacion'] = 'Residuo o Desecho Peligroso con componente RAEE (RESPEL / RAEE)'
    r['clasificacion_corta'] = 'RESPEL / RAEE'
    r['ruta'] = 'respel_raee'
    r['peligroso'] = True
    r['color_ruta'] = 'danger'
    r['badge_color'] = 'danger'
    r['icono_ruta'] = 'bi-radioactive'
    r['normas_aplicables'] = [
        {'codigo': 'Decreto 4741/2005',     'descripcion': 'Prevención y manejo de RESPEL'},
        {'codigo': 'Resolución 1362/2007',  'descripcion': 'Registro de generadores RESPEL'},
        {'codigo': 'Ley 1672/2013',         'descripcion': 'Política pública RAEE'},
        {'codigo': 'Resolución 851/2022',   'descripcion': 'Sistemas de recolección RAEE'},
    ]
    r['descripcion_resultado'] = (
        'El residuo evaluado presenta criterios compatibles con RESPEL y corresponde '
        'además a un aparato eléctrico o electrónico. Requiere gestión con doble énfasis: '
        'régimen de manejo de residuos peligrosos según el Decreto 4741 de 2005 y canales '
        'especializados de RAEE según la Ley 1672 de 2013 y la Resolución 851 de 2022.'
    )


def _set_resultado_respel(r: dict) -> None:
    r['clasificacion'] = 'Residuo o Desecho Peligroso (RESPEL)'
    r['clasificacion_corta'] = 'RESPEL'
    r['ruta'] = 'respel'
    r['peligroso'] = True
    r['color_ruta'] = 'danger'
    r['badge_color'] = 'danger'
    r['icono_ruta'] = 'bi-exclamation-octagon-fill'
    r['normas_aplicables'] = [
        {'codigo': 'Decreto 4741/2005',    'descripcion': 'Prevención y manejo de RESPEL'},
        {'codigo': 'Resolución 1362/2007', 'descripcion': 'Registro de generadores RESPEL'},
    ]
    r['descripcion_resultado'] = (
        'El residuo evaluado presenta criterios compatibles con RESPEL según el '
        'Decreto 4741 de 2005. Su manejo exige cumplir las obligaciones del generador '
        'contempladas en el artículo 10 del mismo decreto, incluyendo almacenamiento '
        'seguro, etiquetado, plan de gestión y entrega a gestor autorizado.'
    )


def _set_resultado_raee(r: dict) -> None:
    r['clasificacion'] = 'Residuo de Aparato Eléctrico o Electrónico (RAEE)'
    r['clasificacion_corta'] = 'RAEE'
    r['ruta'] = 'raee'
    r['color_ruta'] = 'warning'
    r['badge_color'] = 'warning'
    r['icono_ruta'] = 'bi-lightning-charge-fill'
    r['normas_aplicables'] = [
        {'codigo': 'Ley 1672/2013',        'descripcion': 'Política pública para la gestión de RAEE'},
        {'codigo': 'Resolución 851/2022',  'descripcion': 'Sistemas de recolección y gestión de RAEE'},
    ]
    r['descripcion_resultado'] = (
        'El residuo corresponde a la categoría RAEE. No debe disponerse junto con '
        'residuos ordinarios. Debe entregarse a puntos de recolección o sistemas '
        'posconsumo autorizados, bajo el principio de responsabilidad extendida del '
        'productor establecido en la Ley 1672 de 2013.'
    )


def _set_resultado_ambiguo(r: dict) -> None:
    r['ambiguo'] = True
    r['clasificacion'] = 'Clasificación pendiente — Se requiere evaluación de peligrosidad'
    r['clasificacion_corta'] = 'Por determinar'
    r['ruta'] = 'ambiguo'
    r['color_ruta'] = 'secondary'
    r['badge_color'] = 'secondary'
    r['icono_ruta'] = 'bi-question-diamond-fill'
    r['normas_aplicables'] = [
        {'codigo': 'Decreto 4741/2005',     'descripcion': 'Criterios de peligrosidad CRETIP+R'},
        {'codigo': 'Resolución 2184/2019',  'descripcion': 'Separación en la fuente'},
    ]
    r['descripcion_resultado'] = (
        'No es posible determinar la clasificación definitiva del residuo sin evaluar '
        'los criterios de peligrosidad. Por favor complete la evaluación de '
        'características CRETIP+R en el siguiente paso, o consulte a un especialista '
        'ambiental para la caracterización técnica del residuo.'
    )


def _set_resultado_no_peligroso(r: dict, material: str) -> None:
    if material in MATERIALES_ORGANICOS:
        r['clasificacion'] = 'Residuo Orgánico Aprovechable'
        r['clasificacion_corta'] = 'Orgánico'
        r['ruta'] = 'organico'
        r['color_ruta'] = 'success'
        r['badge_color'] = 'success'
        r['icono_ruta'] = 'bi-tree-fill'
        r['normas_aplicables'] = [
            {'codigo': 'Resolución 2184/2019', 'descripcion': 'Código de colores — contenedor verde'},
            {'codigo': 'Decreto 1077/2015',    'descripcion': 'Aprovechamiento de residuos sólidos'},
        ]
        r['descripcion_resultado'] = (
            'El residuo corresponde a materia orgánica aprovechable. Según la Resolución '
            '2184 de 2019 debe depositarse en el contenedor verde. Puede ser valorizado '
            'mediante compostaje, lombricultura u otros procesos de transformación orgánica.'
        )

    elif material in MATERIALES_APROVECHABLES:
        r['clasificacion'] = 'Residuo Aprovechable (Reciclable)'
        r['clasificacion_corta'] = 'Aprovechable'
        r['ruta'] = 'aprovechable'
        r['color_ruta'] = 'info'
        r['badge_color'] = 'info'
        r['icono_ruta'] = 'bi-recycle'
        r['normas_aplicables'] = [
            {'codigo': 'Resolución 2184/2019', 'descripcion': 'Código de colores — contenedor blanco'},
            {'codigo': 'Decreto 1077/2015',    'descripcion': 'Aprovechamiento y reciclaje'},
            {'codigo': 'GTC 24',               'descripcion': 'Guía técnica separación en la fuente (referencia)'},
        ]
        r['descripcion_resultado'] = (
            'El residuo tiene potencial de aprovechamiento o reciclaje. Según la Resolución '
            '2184 de 2019 debe depositarse limpio, seco y sin contaminar en el contenedor '
            'blanco. Apoye a los recicladores de oficio y organizaciones de reciclaje reconocidas.'
        )

    elif material == 'especial':
        r['clasificacion'] = 'Residuo Especial'
        r['clasificacion_corta'] = 'Especial'
        r['ruta'] = 'especial'
        r['color_ruta'] = 'warning'
        r['badge_color'] = 'warning'
        r['icono_ruta'] = 'bi-exclamation-triangle-fill'
        r['normas_aplicables'] = [
            {'codigo': 'Decreto 1077/2015', 'descripcion': 'Residuos especiales'},
        ]
        r['descripcion_resultado'] = (
            'El residuo corresponde a una categoría especial (llantas, escombros, colchones, etc.) '
            'que requiere manejo diferenciado y no puede disponerse con residuos ordinarios. '
            'Consulte la normativa sectorial específica y los operadores autorizados en su municipio.'
        )

    else:
        r['clasificacion'] = 'Residuo No Aprovechable'
        r['clasificacion_corta'] = 'No Aprovechable'
        r['ruta'] = 'no_aprovechable'
        r['color_ruta'] = 'dark'
        r['badge_color'] = 'dark'
        r['icono_ruta'] = 'bi-trash3-fill'
        r['normas_aplicables'] = [
            {'codigo': 'Resolución 2184/2019', 'descripcion': 'Código de colores — contenedor negro'},
            {'codigo': 'Decreto 1077/2015',    'descripcion': 'Servicio público de aseo'},
        ]
        r['descripcion_resultado'] = (
            'El residuo no tiene potencial de aprovechamiento conocido y debe disponerse '
            'en el contenedor negro según la Resolución 2184 de 2019. Será recolectado '
            'por el servicio público de aseo para su disposición final en relleno sanitario autorizado.'
        )


# ---------------------------------------------------------------------------
# Categoría del generador — Resolución 1362/2007
# ---------------------------------------------------------------------------

def _determinar_categoria_generador(datos: dict) -> str:
    try:
        cantidad = float(datos.get('cantidad_mensual', 0) or 0)
        unidad = datos.get('unidad_cantidad', 'kg')

        # Conversión a kilogramos
        factores = {'kg': 1.0, 'ton': 1000.0, 'L': 1.0, 'm3': 1000.0}
        cantidad_kg = cantidad * factores.get(unidad, 1.0)

        if cantidad_kg >= 1000:
            return 'Grande Generador (≥ 1.000 kg/mes)'
        elif cantidad_kg >= 100:
            return 'Mediano Generador (100 – 999 kg/mes)'
        elif cantidad_kg >= 10:
            return 'Pequeño Generador (10 – 99 kg/mes)'
        else:
            return 'Generador de Mínima Cantidad (< 10 kg/mes)'
    except (ValueError, TypeError):
        return 'Categoría no determinada (cantidad no especificada)'


# ---------------------------------------------------------------------------
# Obligaciones del generador — Decreto 4741/2005, Art. 10
# ---------------------------------------------------------------------------

def get_obligaciones_respel(categoria_generador: str) -> list[dict]:
    obligaciones = []

    # Registro ante autoridad ambiental — Resolución 1362/2007
    if 'Grande' in categoria_generador or 'Mediano' in categoria_generador:
        obligaciones.append({
            'titulo': 'Registro de Generadores RESPEL',
            'descripcion': (
                f'Como {categoria_generador}, está obligado a inscribirse en el '
                'Registro de Generadores de Residuos o Desechos Peligrosos ante '
                'la autoridad ambiental competente (ANLA o CAR según jurisdicción).'
            ),
            'norma': 'Resolución 1362/2007',
            'prioridad': 'alta',
        })
    elif 'Pequeño' in categoria_generador:
        obligaciones.append({
            'titulo': 'Verificar obligación de registro RESPEL',
            'descripcion': (
                'Como Pequeño Generador, verifique con su autoridad ambiental local '
                'si existe obligación de registro activa en su jurisdicción. '
                'La Resolución 1362/2007 contempla este rango.'
            ),
            'norma': 'Resolución 1362/2007',
            'prioridad': 'media',
        })

    # Obligaciones base — Decreto 4741/2005, Art. 10
    obligaciones += [
        {
            'titulo': 'Identificación y caracterización del residuo',
            'descripcion': (
                'Identificar plenamente los residuos peligrosos generados en su actividad, '
                'incluyendo su nombre, composición, características de peligrosidad y origen.'
            ),
            'norma': 'Art. 10 num. 1, Decreto 4741/2005',
            'prioridad': 'alta',
        },
        {
            'titulo': 'Almacenamiento seguro',
            'descripcion': (
                'Almacenar los RESPEL en condiciones que prevengan la contaminación del '
                'entorno, la mezcla indebida con otros residuos y los riesgos para la '
                'salud humana y el ambiente. Usar recipientes debidamente identificados.'
            ),
            'norma': 'Art. 10 num. 3, Decreto 4741/2005',
            'prioridad': 'alta',
        },
        {
            'titulo': 'Etiquetado y rotulado de recipientes',
            'descripcion': (
                'Etiquetar todos los recipientes de RESPEL con: nombre del residuo, '
                'características de peligrosidad, fecha de generación, datos del generador '
                'y advertencias de manejo seguro.'
            ),
            'norma': 'Art. 10 num. 4, Decreto 4741/2005',
            'prioridad': 'alta',
        },
        {
            'titulo': 'Plan de Gestión Integral de RESPEL',
            'descripcion': (
                'Elaborar y actualizar un Plan de Gestión de Residuos o Desechos Peligrosos '
                'que incluya estrategias de reducción en la fuente, aprovechamiento y '
                'disposición final adecuada de todos los RESPEL generados.'
            ),
            'norma': 'Art. 10 num. 5, Decreto 4741/2005',
            'prioridad': 'alta',
        },
        {
            'titulo': 'Plan de Contingencia',
            'descripcion': (
                'Contar con un Plan de Contingencia actualizado para el manejo de '
                'accidentes, derrames o emergencias relacionadas con RESPEL, '
                'con protocolos de actuación claros y personal capacitado.'
            ),
            'norma': 'Art. 10 num. 6, Decreto 4741/2005',
            'prioridad': 'media',
        },
        {
            'titulo': 'Entrega exclusiva a gestor autorizado',
            'descripcion': (
                'Entregar los RESPEL únicamente a gestores externos autorizados por '
                'la autoridad ambiental competente. Está prohibido disponer RESPEL en '
                'rellenos sanitarios comunes, alcantarillados o espacios públicos.'
            ),
            'norma': 'Art. 10 num. 7, Decreto 4741/2005',
            'prioridad': 'alta',
        },
        {
            'titulo': 'Conservación de certificados de gestión',
            'descripcion': (
                'Conservar durante el tiempo exigido por la autoridad ambiental las '
                'certificaciones de almacenamiento, aprovechamiento, tratamiento o '
                'disposición final expedidas por los gestores autorizados.'
            ),
            'norma': 'Art. 10 num. 8, Decreto 4741/2005',
            'prioridad': 'media',
        },
        {
            'titulo': 'Hojas de Seguridad (SDS / MSDS)',
            'descripcion': (
                'Disponer y consultar las hojas de datos de seguridad (SDS) de las '
                'sustancias peligrosas que originan los RESPEL. Capacitar al personal '
                'en su lectura e interpretación.'
            ),
            'norma': 'Art. 10 num. 9, Decreto 4741/2005 / GHS-ONU',
            'prioridad': 'media',
        },
    ]

    return obligaciones


# ---------------------------------------------------------------------------
# Estimación del nivel de cumplimiento
# ---------------------------------------------------------------------------

def _estimar_nivel_cumplimiento(resultado: dict, datos: dict) -> str:
    ruta = resultado.get('ruta', '')
    advertencias = len(resultado.get('advertencias', []))
    mezclado = datos.get('mezclado', False)

    if ruta in ('respel', 'respel_raee'):
        if mezclado or advertencias > 2:
            return 'CRÍTICO — Manejo RESPEL obligatorio; se detectaron múltiples factores de riesgo'
        return 'REQUIERE ACCIÓN — Manejo RESPEL obligatorio según Decreto 4741/2005'
    elif ruta == 'raee':
        return 'GESTIÓN ESPECIALIZADA — Requiere canal RAEE autorizado'
    elif ruta == 'ambiguo':
        return 'INDETERMINADO — Necesaria caracterización técnica adicional'
    elif ruta in ('organico', 'aprovechable'):
        return 'CUMPLIMIENTO BÁSICO — Separación en la fuente requerida (Res. 2184/2019)'
    elif ruta == 'especial':
        return 'GESTIÓN DIFERENCIADA — Requiere operador especializado'
    else:
        return 'CUMPLIMIENTO ESTÁNDAR — Disposición ordinaria vía servicio de aseo'


# ---------------------------------------------------------------------------
# Recomendaciones
# ---------------------------------------------------------------------------

def get_recomendaciones(resultado: dict, datos: dict) -> list[str]:
    recomendaciones = []
    ruta = resultado.get('ruta', '')

    if ruta in ('respel', 'respel_raee'):
        recomendaciones += [
            'Consulte el listado de gestores autorizados de RESPEL en su jurisdicción '
            'con la autoridad ambiental competente (ANLA, CAR regional, DAGMA, etc.).',
            'Implemente un sistema interno de rotulado e identificación de contenedores RESPEL.',
            'Capacite periódicamente al personal en manejo seguro y respuesta a emergencias con RESPEL.',
            'Lleve un registro mensual de la generación de RESPEL para control interno y reporte.',
            'No mezcle diferentes tipos de RESPEL sin evaluación técnica previa; '
            'la mezcla puede generar reacciones peligrosas o incrementar el volumen a gestionar.',
        ]

    if ruta in ('raee', 'respel_raee'):
        recomendaciones += [
            'Contacte al fabricante o importador del equipo para conocer su programa de posconsumo.',
            'Identifique puntos de recolección RAEE autorizados en su municipio.',
            'Nunca deposite RAEE en contenedores de residuos ordinarios ni en el espacio público.',
            'Elimine los datos personales de los dispositivos electrónicos antes de entregarlos.',
        ]

    if ruta == 'organico':
        recomendaciones += [
            'Separe los residuos orgánicos en el contenedor verde según la Resolución 2184 de 2019.',
            'Evalúe alternativas de compostaje doméstico o comunitario para valorizar estos residuos.',
            'No mezcle residuos orgánicos con empaques u otros materiales aprovechables.',
        ]

    if ruta == 'aprovechable':
        recomendaciones += [
            'Deposite en el contenedor blanco (residuos aprovechables) según la Resolución 2184 de 2019.',
            'Asegúrese de que el material esté limpio, seco y libre de contaminación orgánica.',
            'Apoye a los recicladores de oficio mediante entrega directa a organizaciones reconocidas.',
        ]

    if ruta == 'no_aprovechable':
        recomendaciones += [
            'Deposite en el contenedor negro (residuos no aprovechables) según la Resolución 2184 de 2019.',
            'Evalúe si alguna fracción del residuo puede separarse previamente para aprovechamiento.',
        ]

    if datos.get('mezclado'):
        recomendaciones.insert(0,
            'PRIORITARIO: Implemente inmediatamente separación en la fuente. '
            'La mezcla de residuos incrementa costos, impide el aprovechamiento y puede '
            'hacer peligrosos residuos que originalmente no lo eran.'
        )

    recomendaciones.append(
        'AVISO EDUCATIVO: Los resultados de este simulador son orientativos y tienen '
        'propósito académico. Para decisiones con implicaciones legales o técnicas, '
        'consulte un profesional ambiental o la autoridad ambiental competente.'
    )

    return recomendaciones
