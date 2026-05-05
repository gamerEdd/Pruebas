# gasto_predictor_selfcontained.py
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# -----------------------------
# 1. Datos de ejemplo entrenables
# -----------------------------
# Cada fila: [tipo (0=ingreso,1=egreso), categoria, dia, mes, diaSemana, monto]
# Ejemplo pequeño de egresos
datos = [
    [1, "Comida", 1, 10, 2, 15.5],
    [1, "Transporte", 1, 10, 2, 2.75],
    [1, "Comida", 2, 10, 3, 20.0],
    [1, "Entretenimiento", 2, 10, 3, 10.0],
    [1, "Comida", 3, 10, 4, 18.0],
    [1, "Transporte", 3, 10, 4, 3.5],
    [1, "Entretenimiento", 3, 10, 4, 12.0],
]

# Convertir a numpy
data = np.array(datos, dtype=object)

# Features: tipo, categoria, dia, mes, diaSemana
X_raw = data[:, 0:5]
# Target: monto
y_raw = data[:, 5].astype(np.float32).reshape(-1, 1)

# -----------------------------
# 2. OneHot encoding para categoria
# -----------------------------
categorias = X_raw[:, 1].reshape(-1,1)
enc = OneHotEncoder(sparse=False)
categorias_encoded = enc.fit_transform(categorias)

# Tipo ya es 1 (egreso), pero lo incluimos
tipo_encoded = X_raw[:, 0].astype(float).reshape(-1,1)

# Fecha features: dia, mes, diaSemana
fecha_features = X_raw[:, 2:5].astype(float)

# Combinar todo
X = np.hstack([tipo_encoded, categorias_encoded, fecha_features])

# Escalado
scaler_X = StandardScaler()
X_scaled = scaler_X.fit_transform(X)

scaler_y = StandardScaler()
y_scaled = scaler_y.fit_transform(y_raw)

# -----------------------------
# 3. Modelo TensorFlow
# -----------------------------
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(X_scaled.shape[1],)),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(1)
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# Entrenar con los datos incluidos
model.fit(X_scaled, y_scaled, epochs=200, batch_size=2, verbose=0)

# -----------------------------
# 4. Exportar a TFLite
# -----------------------------
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with open("gasto_predictor.tflite", "wb") as f:
    f.write(tflite_model)

print("Archivo gasto_predictor.tflite generado con datos internos.")
