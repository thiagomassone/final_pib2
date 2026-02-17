# 🏥 TP Final PIB – App Clínica

Aplicación clínica desarrollada en **Python + Streamlit** para:

- 👤 Gestión de pacientes  
- 🩻 Carga de radiografías de tórax  
- 🧠 Procesamiento de imagen (CLAHE + K-means)  
- 🤖 Inferencia con modelo Random Forest  
- 📦 Compresión con Huffman (`.huf`)  
- 📚 Historia clínica digital  

---

# 📦 Requisitos

- Python 3.10 o superior (recomendado 3.11)
- pip
- Entorno virtual (`venv`)

---

# 🚀 Instalación desde cero

## 1️⃣ Clonar el repositorio
git clone <URL_DEL_REPO>
cd final_pib

## 2️⃣ Crear entorno virtual

### Mac / Linux
python3 -m venv virtual
source virtual/bin/activate

### Windows
python -m venv virtual
virtual\Scripts\activate

## 3️⃣ Instalar dependencias
pip install -r requirements.txt

## 4️⃣ Ejecutar aplicación / Inicializar la base de datos
streamlit run main.py

## 5️⃣ Crear usuario administrador (solo la primera vez)
python bootstrap_admin.py

## Troubleshooting:

### Eliminar base de datos
eliminar app.db o ejecutar rm database/app.db

# 🗂 Estructura del proyecto

final_pib/
│
├── main.py
├── bootstrap_admin.py
│
├── database/
│   └── db.py
│
├── security/
│   └── auth.py
│
├── app_pages/
│   ├── login.py
│   ├── home.py
│   ├── admin_users.py
│   ├── patients.py
│   ├── diagnosis.py
│   └── history.py
│
├── ml_model/
│   └── modelo_random_forest_final.pkl
│
├── image_processing/
│   ├── preprocess.py
│   ├── segmentation.py
│   └── features.py
│
├── compression/
│   ├── huffman_core.py
│   └── huffman_codec.py
│
├── outputs/
│   └── images/
│
├── notebooks/
│   └── COM_compare.ipynb
│
├── requirements.txt
└── README.md
