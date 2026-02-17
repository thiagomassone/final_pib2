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

```
git clone https://github.com/thiagomassone/final_pib2.git
cd final_pib2
```

## 2️⃣ Crear entorno virtual

### Mac / Linux
```
python3 -m venv virtual
source virtual/bin/activate
```

### Windows
```
python -m venv virtual
virtual\Scripts\activate
```

## 3️⃣ Instalar dependencias
```
pip install -r requirements.txt
```

## 4️⃣ Ejecutar aplicación / Inicializar la base de datos
```
streamlit run main.py
```

## 5️⃣ Crear usuario administrador (solo la primera vez)
```
python bootstrap_admin.py
```

## Troubleshooting:

### Eliminar base de datos
eliminar app.db o ejecutar rm database/app.db

# 🗂 Estructura del proyecto

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/04c578cd-359a-4eb1-96a3-3eb21a4d2038" />

