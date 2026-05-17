from __future__ import annotations

import io
from datetime import datetime

from flask import (
    Blueprint, current_app, flash, jsonify, make_response, redirect,
    render_template, request, session, url_for,
)

from app import db
from app.logic import clasificar_residuo
from app.models import Simulacion

try:
    from xhtml2pdf import pisa
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False

main = Blueprint('main', __name__)


# ---------------------------------------------------------------------------
# Páginas informativas
# ---------------------------------------------------------------------------

@main.route('/')
def index():
    return render_template('index.html')


@main.route('/normativa')
def normativa():
    return render_template('normativa.html')


@main.route('/glosario')
def glosario():
    return render_template('glosario.html')


@main.route('/raee-info')
def raee_info():
    return render_template('raee.html')


@main.route('/obligaciones-generador')
def obligaciones_generador():
    resultado = session.get('resultado_final', {})
    datos = session.get('datos_residuo', {})
    return render_template('obligaciones.html', resultado=resultado, datos=datos)


# ---------------------------------------------------------------------------
# Historial de simulaciones
# ---------------------------------------------------------------------------

@main.route('/historial')
def historial():
    page = request.args.get('page', 1, type=int)
    paginacion = (
        Simulacion.query
        .order_by(Simulacion.fecha.desc())
        .paginate(page=page, per_page=12, error_out=False)
    )
    total      = Simulacion.query.count()
    n_respel   = Simulacion.query.filter_by(peligroso=True).count()
    n_raee     = Simulacion.query.filter_by(raee=True).count()
    n_otros    = total - n_respel - n_raee
    return render_template(
        'historial.html',
        paginacion=paginacion,
        total=total,
        n_respel=n_respel,
        n_raee=n_raee,
        n_otros=n_otros,
    )


@main.route('/historial/<int:sim_id>')
def historial_detalle(sim_id: int):
    sim  = Simulacion.query.get_or_404(sim_id)
    datos = _sim_to_datos(sim)
    resultado_data = clasificar_residuo(datos)
    fecha_sim = sim.fecha.strftime('%d/%m/%Y %H:%M')
    return render_template(
        'resultado.html',
        datos=datos,
        resultado=resultado_data,
        fecha=fecha_sim,
        desde_historial=True,
        sim_id=sim_id,
    )


@main.route('/historial/<int:sim_id>/pdf')
def historial_pdf(sim_id: int):
    sim = Simulacion.query.get_or_404(sim_id)
    datos = _sim_to_datos(sim)
    resultado_data = clasificar_residuo(datos)
    fecha_sim = sim.fecha.strftime('%d/%m/%Y %H:%M')
    return _entregar_pdf(datos, resultado_data, fecha_sim)


# ---------------------------------------------------------------------------
# Flujo de simulación — Paso 1
# ---------------------------------------------------------------------------

@main.route('/simulacion', methods=['GET', 'POST'])
def simulacion():
    if request.method == 'POST':
        datos = {
            'nombre_residuo':       request.form.get('nombre_residuo', '').strip(),
            'actividad_generadora': request.form.get('actividad_generadora', '').strip(),
            'sector_fuente':        request.form.get('sector_fuente', ''),
            'estado_fisico':        request.form.get('estado_fisico', ''),
            'cantidad_mensual':     request.form.get('cantidad_mensual', '0'),
            'unidad_cantidad':      request.form.get('unidad_cantidad', 'kg'),
            'lugar_generacion':     request.form.get('lugar_generacion', '').strip(),
            'material_principal':   request.form.get('material_principal', ''),
            'proviene_electronico': 'proviene_electronico' in request.form,
            'contacto_quimico':     'contacto_quimico'     in request.form,
            'mezclado':             'mezclado'              in request.form,
            'envase_contaminado':   'envase_contaminado'   in request.form,
            'criterios_peligrosidad': {},
        }
        if not datos['nombre_residuo']:
            flash('Por favor ingrese el nombre del residuo para continuar.', 'warning')
            return render_template('simulacion.html')

        session['datos_residuo'] = datos
        pre_result = clasificar_residuo(datos)
        session['pre_clasificacion'] = pre_result

        if pre_result.get('requiere_evaluacion_peligrosidad'):
            return redirect(url_for('main.peligrosidad'))
        return redirect(url_for('main.resultado'))

    return render_template('simulacion.html')


# ---------------------------------------------------------------------------
# Flujo de simulación — Paso 2: peligrosidad
# ---------------------------------------------------------------------------

@main.route('/peligrosidad', methods=['GET', 'POST'])
def peligrosidad():
    if 'datos_residuo' not in session:
        flash('Por favor inicie la simulación desde el formulario.', 'info')
        return redirect(url_for('main.simulacion'))

    if request.method == 'POST':
        criterios = {
            'corrosivo':  'criterio_corrosivo'  in request.form,
            'reactivo':   'criterio_reactivo'   in request.form,
            'explosivo':  'criterio_explosivo'  in request.form,
            'toxico':     'criterio_toxico'     in request.form,
            'inflamable': 'criterio_inflamable' in request.form,
            'infeccioso': 'criterio_infeccioso' in request.form,
            'radiactivo': 'criterio_radiactivo' in request.form,
        }
        datos = session['datos_residuo']
        datos['criterios_peligrosidad'] = criterios
        session['datos_residuo'] = datos
        return redirect(url_for('main.resultado'))

    return render_template(
        'peligrosidad.html',
        datos=session.get('datos_residuo', {}),
        pre_clasificacion=session.get('pre_clasificacion', {}),
    )


# ---------------------------------------------------------------------------
# Flujo de simulación — Paso 3: resultado
# ---------------------------------------------------------------------------

@main.route('/resultado')
def resultado():
    if 'datos_residuo' not in session:
        flash('Por favor inicie la simulación desde el formulario.', 'info')
        return redirect(url_for('main.simulacion'))

    datos = session['datos_residuo']
    resultado_data = clasificar_residuo(datos)
    session['resultado_final'] = resultado_data
    _guardar_simulacion(datos, resultado_data)

    fecha_sim = datetime.now().strftime('%d/%m/%Y %H:%M')
    return render_template(
        'resultado.html',
        datos=datos,
        resultado=resultado_data,
        fecha=fecha_sim,
        desde_historial=False,
    )


# ---------------------------------------------------------------------------
# Reportes
# ---------------------------------------------------------------------------

@main.route('/reporte')
def reporte():
    if 'datos_residuo' not in session:
        flash('No hay datos de simulación disponibles.', 'warning')
        return redirect(url_for('main.simulacion'))

    datos = session['datos_residuo']
    resultado_data = session.get('resultado_final') or clasificar_residuo(datos)
    fecha_sim = datetime.now().strftime('%d/%m/%Y %H:%M')
    return render_template('reporte.html', datos=datos, resultado=resultado_data, fecha=fecha_sim)


@main.route('/reporte/pdf')
def reporte_pdf_download():
    if 'datos_residuo' not in session:
        flash('No hay datos de simulación disponibles.', 'warning')
        return redirect(url_for('main.simulacion'))

    datos = session['datos_residuo']
    resultado_data = session.get('resultado_final') or clasificar_residuo(datos)
    fecha_sim = datetime.now().strftime('%d/%m/%Y %H:%M')
    return _entregar_pdf(datos, resultado_data, fecha_sim)


# ---------------------------------------------------------------------------
# Detector IA — Gemini Vision
# ---------------------------------------------------------------------------

@main.route('/detector-ia')
def detector_ia():
    gemini_ok = bool(current_app.config.get('GEMINI_API_KEY', ''))
    return render_template('detector_ia.html', gemini_ok=gemini_ok)


@main.route('/detector-ia/analizar', methods=['POST'])
def detector_ia_analizar():
    from app.ai_detector import analizar_residuo

    imagen = request.files.get('imagen')
    descripcion = request.form.get('descripcion', '').strip()

    imagen_bytes = None
    mime_type = 'image/jpeg'
    if imagen and imagen.filename:
        imagen_bytes = imagen.read()
        mime_type = imagen.content_type or 'image/jpeg'

    if not imagen_bytes and not descripcion:
        return jsonify({'error': 'Proporciona una imagen o una descripción del residuo.'})

    resultado = analizar_residuo(imagen_bytes, descripcion, mime_type)
    return jsonify(resultado)


# ---------------------------------------------------------------------------
# Reinicio
# ---------------------------------------------------------------------------

@main.route('/nueva-simulacion')
def nueva_simulacion():
    session.clear()
    return redirect(url_for('main.simulacion'))


# ---------------------------------------------------------------------------
# Manejadores de errores
# ---------------------------------------------------------------------------

@main.app_errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def error_interno(e):
    return render_template('404.html', error_500=True), 500


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _guardar_simulacion(datos: dict, resultado_data: dict) -> None:
    try:
        criterios = datos.get('criterios_peligrosidad', {})
        sim = Simulacion(
            nombre_residuo       = datos.get('nombre_residuo', ''),
            actividad_generadora = datos.get('actividad_generadora', ''),
            sector_fuente        = datos.get('sector_fuente', ''),
            estado_fisico        = datos.get('estado_fisico', ''),
            cantidad_mensual     = _to_float(datos.get('cantidad_mensual', 0)),
            unidad_cantidad      = datos.get('unidad_cantidad', 'kg'),
            lugar_generacion     = datos.get('lugar_generacion', ''),
            material_principal   = datos.get('material_principal', ''),
            proviene_electronico = bool(datos.get('proviene_electronico', False)),
            contacto_quimico     = bool(datos.get('contacto_quimico', False)),
            mezclado             = bool(datos.get('mezclado', False)),
            envase_contaminado   = bool(datos.get('envase_contaminado', False)),
            criterio_corrosivo   = bool(criterios.get('corrosivo',  False)),
            criterio_reactivo    = bool(criterios.get('reactivo',   False)),
            criterio_explosivo   = bool(criterios.get('explosivo',  False)),
            criterio_toxico      = bool(criterios.get('toxico',     False)),
            criterio_inflamable  = bool(criterios.get('inflamable', False)),
            criterio_infeccioso  = bool(criterios.get('infeccioso', False)),
            criterio_radiactivo  = bool(criterios.get('radiactivo', False)),
            clasificacion_final  = resultado_data.get('clasificacion', ''),
            clasificacion_corta  = resultado_data.get('clasificacion_corta', ''),
            ruta                 = resultado_data.get('ruta', ''),
            categoria_generador  = resultado_data.get('categoria_generador') or '',
            nivel_cumplimiento   = resultado_data.get('nivel_cumplimiento', ''),
            peligroso            = bool(resultado_data.get('peligroso', False)),
            raee                 = bool(resultado_data.get('raee', False)),
        )
        db.session.add(sim)
        db.session.commit()
        session['sim_id'] = sim.id
    except Exception:
        db.session.rollback()


def _sim_to_datos(sim: Simulacion) -> dict:
    return {
        'nombre_residuo':       sim.nombre_residuo or '',
        'actividad_generadora': sim.actividad_generadora or '',
        'sector_fuente':        sim.sector_fuente or '',
        'estado_fisico':        sim.estado_fisico or '',
        'cantidad_mensual':     str(sim.cantidad_mensual or 0),
        'unidad_cantidad':      sim.unidad_cantidad or 'kg',
        'lugar_generacion':     sim.lugar_generacion or '',
        'material_principal':   sim.material_principal or '',
        'proviene_electronico': sim.proviene_electronico or False,
        'contacto_quimico':     sim.contacto_quimico or False,
        'mezclado':             sim.mezclado or False,
        'envase_contaminado':   sim.envase_contaminado or False,
        'criterios_peligrosidad': {
            'corrosivo':  sim.criterio_corrosivo  or False,
            'reactivo':   sim.criterio_reactivo   or False,
            'explosivo':  sim.criterio_explosivo  or False,
            'toxico':     sim.criterio_toxico     or False,
            'inflamable': sim.criterio_inflamable or False,
            'infeccioso': sim.criterio_infeccioso or False,
            'radiactivo': sim.criterio_radiactivo or False,
        },
    }


def _entregar_pdf(datos: dict, resultado_data: dict, fecha_sim: str):
    if not PDF_DISPONIBLE:
        flash('La generación de PDF no está disponible. Use la versión imprimible.', 'warning')
        return redirect(url_for('main.reporte'))

    html_string = render_template(
        'reporte_pdf.html',
        datos=datos,
        resultado=resultado_data,
        fecha=fecha_sim,
    )
    pdf_bytes = _html_to_pdf(html_string)
    if pdf_bytes is None:
        flash('Error al generar el PDF. Use la versión imprimible.', 'danger')
        return redirect(url_for('main.reporte'))

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f'SimuRESPEL-{datetime.now().strftime("%Y%m%d-%H%M")}.pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


def _html_to_pdf(html_string: str) -> bytes | None:
    try:
        result = io.BytesIO()
        status = pisa.CreatePDF(
            io.BytesIO(html_string.encode('UTF-8')),
            dest=result,
            encoding='UTF-8',
        )
        if status.err:
            return None
        result.seek(0)
        return result.read()
    except Exception:
        return None


def _to_float(value) -> float:
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0
