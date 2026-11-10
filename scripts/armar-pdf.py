#!/usr/bin/env python3
"""Arma el PDF de evidencias a partir de docs/evidencias/<LETRA>/CRITERIO-descripcion.png.
Las capturas se agrupan por persona (P1 a P6), según quién entrega cada criterio.

Uso:
    python scripts/armar-pdf.py
    python scripts/armar-pdf.py --estricto      # falla si falta alguna captura

Necesita: pip install reportlab pillow
"""
import argparse
import io
import re
import sys
from datetime import date
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

RAIZ = Path(__file__).resolve().parent.parent

INTEGRANTES = [
    ("José Daniel Paz Ortega", "1200022"),
    ("Giancarlo Ortega", "1230222"),
    ("Jorge Francisco Muñoz Portela", "1177523"),
    ("Julio Javier Robles García", "1248823"),
    ("Ana Sofía Asturias To", "1078123"),
    ("Ana Lucía Chávez", "1067423"),
]

PERSONAS = [
    ("P1", "Giancarlo Ortega"),
    ("P2", "José Daniel Paz Ortega"),
    ("P3", "Ana Sofía Asturias To"),
    ("P4", "Julio Javier Robles García"),
    ("P5", "Ana Lucía Chávez"),
    ("P6", "Jorge Francisco Muñoz Portela"),
]

# Quién entrega cada criterio, según la tabla del plan general.
RESPONSABLES = {
    "A1": "P1", "A2": "P2", "A3": "P3", "A4": "P4", "A5": "P5",
    "B1": "P1", "B2": "P2", "B3": "P2", "B4": "P3",
    "C1": "P6", "C2": "P6", "C3": "P6",
    "D1": "P5", "D2": "P5", "D3": "P5", "D4": "P5", "D5": "P5",
    "E1": "P6", "E2": "P4", "E3": "P4", "E4": "P4", "E5": "P6", "E6": "P6",
    "F1": "P6", "F2": "P6", "F3": "P6", "F4": "P6",
    "G1": "P5", "G2": "P5", "G3": "P5",
}

# Cuando un criterio tiene capturas de más de una persona, se decide por el nombre del archivo.
PALABRA_A_PERSONA = {
    "A4": [("interfaz", "P3")],
    "B3": [("pacientes", "P1"), ("frontend", "P3")],
}

# Títulos cortos de las capturas, solo el nombre de lo que se ve.
TITULOS = {
    "A1": "Historial de commits",
    "A2": "README",
    "A3": "Diagrama de arquitectura",
    "A4": "Carnés",
    "A5": "Clúster y namespace",
    "B1": "Pacientes",
    "B2": "Citas",
    "B3": "Dockerfile",
    "B4": "Frontend",
    "C1": "Imágenes con ruta de Artifact Registry",
    "C2": "Listado del repositorio",
    "C3": "Manifiestos",
    "D1": "Archivos de Terraform",
    "D2": "Variables",
    "D3": "terraform plan",
    "D4": "terraform apply",
    "D5": "Nodos spot",
    "E1": "kubectl get all",
    "E2": "ConfigMap en un Pod",
    "E3": "Secret en un Pod",
    "E4": "Volumen persistente",
    "E5": "IP pública desde el celular",
    "E6": "Tráfico por DNS",
    "F1": "Tres réplicas",
    "F2": "Pod borrado",
    "F3": "Rolling update",
    "F4": "Logs",
    "G1": "Estimación de costo",
    "G2": "terraform destroy",
    "G3": "Facturación",
}

# Título más preciso para capturas que comparten criterio.
TITULOS_POR_ARCHIVO = {
    "A2-readme-caso-integrantes": "README, caso e integrantes",
    "A2-readme-instrucciones": "README, instrucciones",
    "A4-carnes-en-bd": "Carnés en la base de datos",
    "A4-carnes-en-interfaz": "Carnés en la interfaz",
    "B1-crear-y-listar-pacientes": "Pacientes, crear y listar",
    "B1-editar-y-eliminar-pacientes": "Pacientes, editar y eliminar",
    "B2-crear-y-listar-citas": "Citas, crear y listar",
    "B2-editar-y-eliminar-citas": "Citas, editar y eliminar",
    "B3-dockerfile-citas": "Dockerfile de citas",
    "B3-dockerfile-pacientes": "Dockerfile de pacientes",
    "B3-dockerfile-frontend": "Dockerfile del frontend",
    "B3-docker-images": "docker images",
    "B4-frontend-ambos-servicios": "Frontend con pacientes y citas",
}

# Código, puntos y descripción de cada criterio, en el orden de la rúbrica.
CRITERIOS = [
    ("A1", 4, "Historial de commits en al menos tres días distintos"),
    ("A2", 3, "README con el caso, los integrantes y las instrucciones"),
    ("A3", 3, "Diagrama de arquitectura"),
    ("A4", 2, "Carné de los integrantes en la base de datos y en la interfaz"),
    ("A5", 2, "Clúster y namespace con el identificador del equipo"),
    ("B1", 5, "Microservicio de pacientes con CRUD"),
    ("B2", 5, "Microservicio de citas con CRUD"),
    ("B3", 3, "Un contenedor y un Dockerfile por microservicio"),
    ("B4", 5, "Frontend con los datos de ambos microservicios"),
    ("C1", 4, "Imágenes etiquetadas con la ruta completa de Artifact Registry"),
    ("C2", 3, "Imágenes publicadas y listado del repositorio"),
    ("C3", 3, "Manifiestos que solo usan imágenes de Artifact Registry"),
    ("D1", 5, "Archivos de Terraform del clúster, el node pool y el registro"),
    ("D2", 4, "Variables sin valores sensibles"),
    ("D3", 3, "Salida de terraform plan"),
    ("D4", 3, "Salida de terraform apply"),
    ("D5", 3, "Nodos spot"),
    ("E1", 5, "Todo desplegado y en ejecución"),
    ("E2", 3, "ConfigMap consumido por un Pod"),
    ("E3", 3, "Secret consumido por un Pod"),
    ("E4", 5, "Volumen persistente: los datos sobreviven al borrar el Pod"),
    ("E5", 4, "IP pública accesible desde un navegador externo"),
    ("E6", 2, "Tráfico entre servicios por DNS"),
    ("F1", 3, "Tres réplicas de forma declarativa"),
    ("F2", 2, "Un Pod borrado se recrea solo"),
    ("F3", 3, "Rolling update de la imagen"),
    ("F4", 2, "Logs de un Pod"),
    ("G1", 3, "Estimación del costo mensual antes del despliegue"),
    ("G2", 3, "terraform destroy con su salida"),
    ("G3", 2, "Facturación con el gasto final"),
]

EXTENSIONES = {".png", ".jpg", ".jpeg"}
PATRON = re.compile(r"^([A-G]\d)(?:[-_ ].*)?$", re.IGNORECASE)


def buscar_capturas(carpeta):
    capturas = {}
    for archivo in sorted(carpeta.rglob("*")):
        if archivo.suffix.lower() not in EXTENSIONES:
            continue
        m = PATRON.match(archivo.stem)
        if not m:
            print(f"aviso: el nombre {archivo.name} no empieza con un código de criterio, se ignora")
            continue
        capturas.setdefault(m.group(1).upper(), []).append(archivo)
    return capturas


def persona_de(codigo, archivo):
    nombre = archivo.stem.lower()
    for palabra, persona in PALABRA_A_PERSONA.get(codigo, []):
        if palabra in nombre:
            return persona
    return RESPONSABLES[codigo]


def titulo_de(codigo, archivo):
    return TITULOS_POR_ARCHIVO.get(archivo.stem, TITULOS[codigo])


def imagen_para_pdf(ruta, ancho_max_cm, alto_max_cm):
    img = Image.open(ruta).convert("RGB")
    if img.height > img.width:
        # Capturas de celular: verticales, se dejan más altas para que se lean.
        alto_max_cm = 18
    if img.width > 1800:
        img = img.resize((1800, round(img.height * 1800 / img.width)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    buf.seek(0)
    escala = min(ancho_max_cm * cm / img.width, alto_max_cm * cm / img.height)
    return RLImage(buf, width=img.width * escala, height=img.height * escala)


def estilos():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("titulo", parent=base["Title"], fontName="Helvetica-Bold",
                                 fontSize=24, leading=30, alignment=TA_CENTER),
        "centro": ParagraphStyle("centro", parent=base["Normal"], fontName="Helvetica",
                                 fontSize=13, leading=18, alignment=TA_CENTER),
        "seccion": ParagraphStyle("seccion", parent=base["Heading1"], fontName="Helvetica-Bold",
                                  fontSize=18, spaceBefore=6, spaceAfter=10),
        "criterio": ParagraphStyle("criterio", parent=base["Heading2"], fontName="Helvetica-Bold",
                                   fontSize=12, spaceBefore=10, spaceAfter=6),
        "texto": ParagraphStyle("texto", parent=base["Normal"], fontName="Helvetica",
                                fontSize=11, leading=15),
    }


def portada(est, hoy):
    filas = [[nombre, carne] for nombre, carne in INTEGRANTES]
    tabla = Table(filas, colWidths=[9 * cm, 3.5 * cm])
    tabla.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [
        Spacer(1, 3 * cm),
        Paragraph("Universidad Rafael Landívar", est["centro"]),
        Paragraph("Virtualización, sección 02", est["centro"]),
        Spacer(1, 3 * cm),
        Paragraph("Clínica veterinaria en Kubernetes", est["titulo"]),
        Paragraph("Evidencias del proyecto final", est["centro"]),
        Spacer(1, 1 * cm),
        Paragraph("Equipo Maximos", est["centro"]),
        Spacer(1, 2.5 * cm),
        tabla,
        Spacer(1, 3 * cm),
        Paragraph(hoy, est["centro"]),
        PageBreak(),
    ]


def construir(args):
    est = estilos()
    carpeta = Path(args.evidencias)
    capturas = buscar_capturas(carpeta)
    hoy = date.today().strftime("%d/%m/%Y")

    historia = portada(est, hoy)

    faltan = []
    por_persona = {clave: [] for clave, _ in PERSONAS}
    for codigo, _puntos, _descripcion in CRITERIOS:
        fotos = capturas.get(codigo, [])
        if not fotos:
            faltan.append(codigo)
        for foto in fotos:
            por_persona[persona_de(codigo, foto)].append((codigo, foto))

    for clave, nombre in PERSONAS:
        fotos = por_persona[clave]
        if not fotos:
            continue
        bloques = [Paragraph(f"{clave}. {nombre}", est["seccion"])]
        for codigo, foto in fotos:
            titulo = Paragraph(f"{codigo}. {titulo_de(codigo, foto)}", est["criterio"])
            bloques.append(KeepTogether([titulo, imagen_para_pdf(foto, 17, 12)]))
        historia += bloques + [PageBreak()]

    if historia and isinstance(historia[-1], PageBreak):
        historia.pop()

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(salida), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title="Evidencias del proyecto final - Maximos",
                            author="Equipo Maximos")
    doc.build(historia)

    total = sum(1 for c in capturas.values() for _ in c)
    print(f"PDF generado: {salida} ({total} capturas)")
    if faltan:
        print("Criterios sin captura: " + ", ".join(faltan))
        if args.estricto:
            sys.exit(1)
    else:
        print("Estan los 30 criterios.")
    print("Antes de entregar: revisar que cada captura muestre el reloj del sistema y gcloud config list,")
    print("que G1 sea anterior al primer despliegue y que D3 (plan) sea anterior a D4 (apply).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Arma el PDF de evidencias")
    ap.add_argument("--evidencias", default=str(RAIZ / "docs" / "evidencias"))
    ap.add_argument("--salida", default=str(RAIZ / "docs" / "Evidencias-Proyecto-Final-Maximos.pdf"))
    ap.add_argument("--estricto", action="store_true")
    construir(ap.parse_args())
