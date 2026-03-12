from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)
    transacciones = relationship("Transaccion", back_populates="categoria")


class Tarjeta(Base):
    __tablename__ = "tarjetas"
    id = Column(Integer, primary_key=True)
    banco = Column(String, nullable=False)
    nombre_alias = Column(String)
    terminacion = Column(String(4))
    dia_corte = Column(Integer, nullable=False)
    dias_limite_pago = Column(Integer, nullable=False)
    limite_credito = Column(Float)
    transacciones = relationship("Transaccion", back_populates="tarjeta")


class Transaccion(Base):
    __tablename__ = "transacciones"
    id = Column(Integer, primary_key=True)
    tarjeta_id = Column(Integer, ForeignKey("tarjetas.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    fecha = Column(Date, nullable=False)
    descripcion = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    tipo_movimiento = Column(String, nullable=False)  # 'cargo' o 'abono'
    es_msi = Column(Boolean, default=False)
    plazo_msi = Column(Integer, default=1)

    tarjeta = relationship("Tarjeta", back_populates="transacciones")
    categoria = relationship("Categoria", back_populates="transacciones")
    parcialidades = relationship("ParcialidadMSI", back_populates="transaccion")


class ParcialidadMSI(Base):
    __tablename__ = "parcialidades_msi"
    id = Column(Integer, primary_key=True)
    transaccion_id = Column(Integer, ForeignKey("transacciones.id"), nullable=False)
    numero_pago = Column(Integer, nullable=False)
    monto_parcialidad = Column(Float, nullable=False)
    mes_cobro = Column(Date, nullable=False)
    transaccion = relationship("Transaccion", back_populates="parcialidades")


class PerfilFinanciero(Base):
    __tablename__ = "perfil_financiero"
    id = Column(Integer, primary_key=True)
    ingreso_mensual = Column(Float, nullable=False, default=0.0)
