#!/usr/bin/env python3
"""Arma el PDF final a partir de docs/evidencias/<LETRA>/CRITERIO-descripcion.png.

El PDF lleva la portada, un informe corto y un anexo con las capturas agrupadas por
persona (P1 a P6), según quién entrega cada criterio de la rúbrica.

Uso:
    python scripts/armar-pdf.py
    python scripts/armar-pdf.py --estricto      # falla si falta alguna captura

Necesita: pip install reportlab pillow
"""
import argparse
import io
import re
import sys
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable,
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

REPO = "https://github.com/Keinaro/proyecto-final-maximos"
REGISTRO = "us-central1-docker.pkg.dev/veterinaria-maximos-final/vet-repo"
IP_PUBLICA = "35.224.209.199"

# Orden de la portada.
PORTADA_INTEGRANTES = [
    "Ana Lucía Chávez Penagos - 1067423",
    "Julio Javier Robles García - 1248823",
    "Ana Sofía Asturias To - 1078123",
    "Jorge Francisco Muñoz Portela - 1177523",
    "Daniel Paz - 1200022",
    "Giancarlo Ortega - 1230222",
]

# Clave, nombre, carné, área de trabajo.
PERSONAS = [
    ("P1", "Giancarlo Ortega Bonilla", "1230222", "Microservicio Pacientes"),
    ("P2", "José Daniel Paz Ortega", "1200022", "Microservicio Citas, README y PDF"),
    ("P3", "Ana Sofía Asturias To", "1078123", "Frontend y diagrama"),
    ("P4", "Julio Javier Robles García", "1248823", "Base de datos y configuración"),
    ("P5", "Ana Lucía Chávez Penagos", "1067423", "Terraform y costos"),
    ("P6", "Jorge Francisco Muñoz Portela", "1177523", "Kubernetes, imágenes y operación"),
]

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

# Título corto de cada criterio: solo el nombre de lo que se ve.
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

# Título más preciso para las capturas que comparten criterio.
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
    "D1-lista-de-archivos-terraform": "Archivos de Terraform en el repositorio",
    "D1-main-tf-node-pool-spot": "main.tf, grupo de nodos Spot",
    "D2-variables-tf-parte-1": "variables.tf, primera parte",
    "D2-variables-tf-parte-2": "variables.tf, segunda parte",
    "D5-nodos-spot": "Nodos spot, etiqueta gke-spot",
    "D5-nodos-spot-kubectl-ana-lucia": "Nodos spot, kubectl get nodes",
}

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
        alto_max_cm = 17
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
                                 fontSize=22, leading=28, alignment=TA_CENTER),
        "centro": ParagraphStyle("centro", parent=base["Normal"], fontName="Helvetica",
                                 fontSize=13, leading=19, alignment=TA_CENTER),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold",
                             fontSize=16, leading=20, spaceBefore=4, spaceAfter=10),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold",
                             fontSize=12.5, leading=16, spaceBefore=12, spaceAfter=5),
        "texto": ParagraphStyle("texto", parent=base["Normal"], fontName="Helvetica",
                                fontSize=10.5, leading=15, spaceAfter=6),
        "dato": ParagraphStyle("dato", parent=base["Normal"], fontName="Helvetica",
                               fontSize=10.5, leading=15, spaceAfter=2),
        "captura": ParagraphStyle("captura", parent=base["Normal"], fontName="Helvetica-Bold",
                                  fontSize=11, leading=14, spaceBefore=10, spaceAfter=5),
    }


def tabla(filas, anchos, encabezado=True):
    t = Table(filas, colWidths=anchos, repeatRows=1 if encabezado else 0)
    estilo = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if encabezado:
        estilo += [("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                   ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.93, 0.93, 0.93))]
    t.setStyle(TableStyle(estilo))
    return t


class Portada(Flowable):
    """Portada igual a las de los proyectos anteriores: el bloque de la universidad arriba a la
    izquierda, el título en negrita al centro, los integrantes a la derecha y la fecha abajo.
    Las posiciones se miden desde el borde de la hoja, con margen de una pulgada."""

    ENCABEZADO = [
        "Universidad Rafael Landívar",
        "Facultad de Ingeniería",
        "Ingeniería en Informática y de Sistemas",
        "Virtualización",
        "Sección No. 2",
        "Ing. Guillermo Zepeda",
    ]
    TITULO = ["Proyecto final", "Clínica veterinaria en Kubernetes con Terraform"]
    FECHA = "Guatemala, 10 de noviembre de 2026"
    MARGEN = 72
    INTERLINEA = 15.8

    def wrap(self, ancho, alto):
        self.ancho, self.alto = ancho, alto
        return ancho, alto

    def _y(self, desde_arriba):
        # Del borde superior de la hoja a la coordenada local del marco (margen de 2 cm abajo).
        return (A4[1] - desde_arriba) - 2 * cm

    def draw(self):
        c = self.canv
        izquierda = self.MARGEN - 2 * cm
        derecha = A4[0] - self.MARGEN - 2 * cm
        centro = A4[0] / 2 - 2 * cm

        c.setFont("Helvetica", 11)
        for i, linea in enumerate(self.ENCABEZADO):
            c.drawString(izquierda, self._y(89 + i * self.INTERLINEA), linea)

        c.setFont("Helvetica-Bold", 12)
        for i, linea in enumerate(self.TITULO):
            c.drawCentredString(centro, self._y(396 + i * 21), linea)

        c.setFont("Helvetica", 11)
        for i, nombre in enumerate(PORTADA_INTEGRANTES):
            c.drawRightString(derecha, self._y(642 + i * self.INTERLINEA), nombre)

        c.drawCentredString(centro, self._y(755), self.FECHA)


def portada(est):
    return [Portada(), PageBreak()]


def informe(est):
    p = lambda texto: Paragraph(texto, est["texto"])
    d = lambda texto: Paragraph(texto, est["dato"])
    h2 = lambda texto: Paragraph(texto, est["h2"])
    enlace = lambda url: f'<link href="{url}" color="#1a56b0">{url}</link>'

    responsables = [["Área", "Responsable", "Carné"]]
    for i, (clave, nombre, carne, area) in enumerate(PERSONAS, start=1):
        responsables.append([f"{i}. {area}", nombre, carne])

    rutas = [
        ["Ruta pública", "Destino", "Puerto"],
        ["/", "archivos del frontend", "80"],
        ["/api/pacientes", "pacientes", "8080"],
        ["/api/integrantes", "pacientes", "8080"],
        ["/api/citas", "citas", "8080"],
        ["/api/health/pacientes y /api/health/citas", "/health de cada servicio", "8080"],
    ]

    return [
        Paragraph("Informe — Proyecto final: clínica veterinaria en Kubernetes", est["h1"]),
        d("<b>Curso:</b> Virtualización, Ingeniería en Informática y de Sistemas, Universidad Rafael Landívar"),
        d("<b>Grupo:</b> Maximos"),
        d("<b>Entrega:</b> martes 10 de noviembre de 2026"),
        d(f"<b>Repositorio:</b> {enlace(REPO)}"),
        d(f"<b>Imágenes:</b> {REGISTRO}"),
        d("<b>Clúster:</b> gke-maximos, zona us-central1-a, proyecto de Google Cloud veterinaria-maximos-final"),
        Spacer(1, 10),
        tabla(responsables, [7.2 * cm, 6.8 * cm, 2.6 * cm]),

        h2("1. Qué es"),
        p("La aplicación lleva el registro de los pacientes de una clínica veterinaria (las mascotas y sus "
          "propietarios) y de las citas de cada uno. Se divide en dos microservicios, Pacientes y Citas, un "
          "frontend web y una base de datos PostgreSQL. Los microservicios están escritos en Python con "
          "FastAPI y el frontend es HTML, CSS y JavaScript servidos por nginx. Todo corre en contenedores: "
          "en la computadora con Docker Compose, y en Google Cloud sobre un clúster de Kubernetes (GKE) que "
          "se crea con Terraform."),

        h2("2. Arquitectura"),
        p(f"El navegador solo habla con el frontend, que es el único componente con IP pública (un Service "
          f"LoadBalancer, {IP_PUBLICA}). El nginx del frontend reenvía las rutas que empiezan con /api a los "
          "microservicios usando el nombre DNS de cada Service. Pacientes, Citas y la base de datos son "
          "ClusterIP, así que no se pueden alcanzar desde afuera del clúster."),
        tabla(rutas, [7.6 * cm, 6.2 * cm, 2.8 * cm]),
        Spacer(1, 6),
        p("Los dos microservicios llegan a PostgreSQL por el Service db, en el puerto 5432."),

        h2("3. Datos y configuración"),
        p("La base tiene tres tablas: integrantes (nombre y carné de los seis), pacientes y citas. Cada cita "
          "apunta a un paciente con una llave foránea y ON DELETE RESTRICT, así que un paciente con citas no "
          "se puede borrar: Pacientes responde 409. Si se crea una cita para un paciente que no existe, Citas "
          "responde 400. Los datos viven en un volumen persistente (PVC de 1 Gi) y siguen ahí si el Pod de la "
          "base se recrea."),
        p("La configuración que no es secreta (puerto, host y nombre de la base) está en el ConfigMap "
          "app-config. El usuario y la contraseña están en el Secret db-secret, que no se sube al repositorio. "
          "Todo está en el namespace maximos."),

        h2("4. Infraestructura"),
        p("Terraform crea un clúster GKE Standard de una sola zona (gke-maximos, us-central1-a), un grupo de "
          "nodos con dos máquinas e2-small Spot, el repositorio de imágenes vet-repo en Artifact Registry y la "
          "cuenta de servicio de los nodos, con permiso para leer imágenes y enviar logs y métricas. Los "
          "archivos de Terraform no tienen valores sensibles: el proyecto de Google Cloud se pasa como "
          "variable."),

        h2("5. Imágenes y despliegue"),
        p("Cada servicio tiene su propio Dockerfile y su propia imagen, construida para linux/amd64 y publicada "
          "en Artifact Registry con una etiqueta de versión (v1.0.0), nunca latest. Los manifiestos de "
          "Kubernetes solo usan imágenes de Artifact Registry, por eso la imagen de PostgreSQL también se "
          "copió al repositorio. El despliegue completo se hace con scripts/deploy.sh."),
        p("Para la operación se probó escalar Pacientes a tres réplicas editando el YAML, borrar un Pod y ver "
          "cómo se recrea, y un rolling update de Pacientes de la versión v1.0.0 a la v1.1.0."),

        h2("6. Costos"),
        p("En la calculadora de Google Cloud la estimación fue de 108.28 USD al mes para este despliegue. El "
          "gasto real hasta el 10 de noviembre fue de 1.07 USD. Al terminar se borran los recursos de "
          "Kubernetes con scripts/deploy.sh delete y se destruye la infraestructura con terraform destroy, "
          "para que el clúster no siga cobrando."),

        h2("7. Cómo ejecutarlo"),
        p("En local hace falta Docker con Compose: se copia .env.example a .env, se escriben el usuario y la "
          "contraseña de la base y se corre docker compose up --build. La aplicación queda en "
          "http://localhost:8080."),
        p("En Google Cloud se corren terraform init, plan y apply dentro de la carpeta terraform. Después se "
          "ejecutan scripts/build-push.sh y scripts/deploy.sh, y se abre en el navegador la IP pública del "
          "frontend. Los pasos completos están en el README del repositorio."),
        PageBreak(),
    ]


def anexo(est, por_persona):
    historia = [Paragraph("Anexo — Evidencias", est["h1"]),
                Paragraph("Las capturas están agrupadas por persona. Las de la terminal del clúster muestran el reloj "
                          "del sistema y la salida de gcloud config list con el proyecto del equipo. Las de "
                          "Terraform y costos (D1, D2, G1, G3 y una de D5) las tomó Ana Lucía en su "
                          "computadora.", est["texto"])]
    primera = True
    for clave, nombre, _carne, area in PERSONAS:
        fotos = por_persona[clave]
        if not fotos:
            continue
        if not primera:
            historia.append(PageBreak())
        primera = False
        historia.append(Paragraph(f"{clave} · {nombre} · {area}", est["h2"]))
        for codigo, foto in fotos:
            titulo = Paragraph(f"{codigo}. {titulo_de(codigo, foto)}", est["captura"])
            historia.append(KeepTogether([titulo, imagen_para_pdf(foto, 16.5, 11)]))
    return historia


def construir(args):
    est = estilos()
    capturas = buscar_capturas(Path(args.evidencias))

    faltan = []
    por_persona = {clave: [] for clave, *_ in PERSONAS}
    for codigo, _puntos, _descripcion in CRITERIOS:
        fotos = capturas.get(codigo, [])
        if not fotos:
            faltan.append(codigo)
        for foto in fotos:
            por_persona[persona_de(codigo, foto)].append((codigo, foto))

    historia = portada(est) + informe(est) + anexo(est, por_persona)

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(salida), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title="Proyecto final - Clínica veterinaria en Kubernetes - Maximos",
                            author="Equipo Maximos")
    doc.build(historia)

    total = sum(len(c) for c in capturas.values())
    print(f"PDF generado: {salida} ({total} capturas)")
    if faltan:
        print("Criterios sin captura: " + ", ".join(faltan))
        if args.estricto:
            sys.exit(1)
    else:
        print("Estan los 30 criterios.")
    print("Antes de entregar: revisar que las capturas de la terminal muestren el reloj del sistema y")
    print("gcloud config list, que G1 sea anterior al primer despliegue y que D3 (plan) sea anterior a D4 (apply).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Arma el PDF final")
    ap.add_argument("--evidencias", default=str(RAIZ / "docs" / "evidencias"))
    ap.add_argument("--salida", default=str(RAIZ / "docs" / "Evidencias-Proyecto-Final-Maximos.pdf"))
    ap.add_argument("--estricto", action="store_true")
    construir(ap.parse_args())
