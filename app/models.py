from datetime import datetime
from app import db


class Simulacion(db.Model):
    __tablename__ = 'simulaciones'

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Datos básicos del residuo
    nombre_residuo = db.Column(db.String(200), nullable=False)
    actividad_generadora = db.Column(db.String(300))
    sector_fuente = db.Column(db.String(100))
    estado_fisico = db.Column(db.String(50))
    cantidad_mensual = db.Column(db.Float, default=0.0)
    unidad_cantidad = db.Column(db.String(20), default='kg')
    lugar_generacion = db.Column(db.String(200))
    material_principal = db.Column(db.String(100))

    # Banderas de condiciones especiales
    proviene_electronico = db.Column(db.Boolean, default=False)
    contacto_quimico = db.Column(db.Boolean, default=False)
    mezclado = db.Column(db.Boolean, default=False)
    envase_contaminado = db.Column(db.Boolean, default=False)

    # Criterios de peligrosidad evaluados (CRETIP+R)
    criterio_corrosivo = db.Column(db.Boolean, default=False)
    criterio_reactivo = db.Column(db.Boolean, default=False)
    criterio_explosivo = db.Column(db.Boolean, default=False)
    criterio_toxico = db.Column(db.Boolean, default=False)
    criterio_inflamable = db.Column(db.Boolean, default=False)
    criterio_infeccioso = db.Column(db.Boolean, default=False)
    criterio_radiactivo = db.Column(db.Boolean, default=False)

    # Resultado de la clasificación
    clasificacion_final = db.Column(db.String(150))
    clasificacion_corta = db.Column(db.String(50))
    ruta = db.Column(db.String(50))
    categoria_generador = db.Column(db.String(80))
    nivel_cumplimiento = db.Column(db.String(200))
    peligroso = db.Column(db.Boolean, default=False)
    raee = db.Column(db.Boolean, default=False)

    def __repr__(self) -> str:
        return f'<Simulacion #{self.id} | {self.nombre_residuo} | {self.clasificacion_corta}>'
