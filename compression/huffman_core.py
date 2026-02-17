import numpy as np

def histograma(img: np.ndarray) -> np.ndarray:
    """
    Histograma para imagen uint8 (256 bins).
    Devuelve counts (no normalizado).
    """
    if img.dtype != np.uint8:
        img = img.astype(np.uint8)
    return np.bincount(img.ravel(), minlength=256).astype(np.int64)


def findCode(tree, val):
    code, padre = tree[val]
    if padre != 'r':
        code = findCode(tree, padre) + code
    return code


def HuffmanEncoding(img):
    # Paso 1: Tamaño de la imagen y rango de niveles de grises
    if img.ndim != 2:
        raise ValueError("HuffmanEncoding espera una imagen 2D (grayscale).")
    if img.dtype != np.uint8:
        img = img.astype(np.uint8)

    fil, col = img.shape
    pixeles = fil * col

    # Paso 2: Calculo el histograma normalizado
    hist = histograma(img) / pixeles

    # Paso 3: Genero dos listas vacias para las frecuencias y para la intensidad correspondiente
    lista_histograma = []
    lista_intensidad = []

    # Paso 4: Ingreso valores en las listas
    for i in range(len(hist)):
        if hist[i] != 0:
            lista_histograma.append([hist[i], i])
            lista_intensidad.append(i)

    # Paso 5: Creo mi árbol y el contador para los nodos
    tree = {}
    k = 0  # para ir poniendo nombre a los nodos

    # Paso 6: Hasta que quede sólo un elemento en lista_histograma
    while len(lista_histograma) > 1:
        # 6.1) Ordeno histograma según la frecuencia (hist(i)) de menor a mayor
        lista_histograma.sort(key=lambda x: x[0])

        # 6.2) Selecciono los primeros dos elementos más chicos
        a1 = lista_histograma.pop(0)
        a2 = lista_histograma.pop(0)

        # 6.3) Saco la frecuencia conjunta
        fconj = a1[0] + a2[0]

        # 6.4) Le asigno un nombre (nombre del nodo)
        k += 1
        kstr = str(k)
        nstr = 'n' + kstr

        # 6.5) Los vuelvo a agregar a la lista para que se reordenen en el while
        lista_histograma.append([fconj, nstr])

        # 6.6) Armo el arbol
        tree[a1[1]] = ['0', nstr]
        tree[a2[1]] = ['1', nstr]

    # Paso 7: Finalizo el árbol
    tree[nstr] = ['', 'r']

    # Paso 8: Inicio el diccionario con la codificación
    dicc = {}

    # Paso 9: Codifico el árbol
    for a in lista_intensidad:
        code = findCode(tree, a)
        dicc[a] = code

    # Paso 10: Recorro la imagen y genero una lista de string con los valores que le corresponden
    vector = img.flatten()
    comprimida = ''.join([dicc[int(value)] for value in vector])

    size_in_bits = len(comprimida)
    size_in_bytes = size_in_bits / 8

    return comprimida, dicc, img.shape, size_in_bytes


def HuffmanDec(comprimida, dicc, shape):
    # Crear un diccionario inverso para decodificación
    rev_dicc = {v: k for k, v in dicc.items()}
    current_code = ""
    descomprimida = []

    for bit in comprimida:
        current_code += bit
        if current_code in rev_dicc:
            descomprimida.append(rev_dicc[current_code])
            current_code = ""

    # Convertir la lista de valores a una matriz con la forma original
    descomprimida = np.array(descomprimida, dtype=np.uint8).reshape(shape)

    return descomprimida
