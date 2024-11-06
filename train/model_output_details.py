import tensorflow as tf

# Ruta del modelo TFLite
#model_path = '/home/drone/Desktop/tflite1/Sample_TFLite_model/modeloDeteccion2epc.tflite'
model_path = 'model.tflite'

# Cargar el modelo TFLite
interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Obtener detalles de las salidas del modelo
output_details = interpreter.get_output_details()

# Imprimir los detalles de las salidas
print("Detalles de las salidas del modelo:")
for idx, output in enumerate(output_details):
    print(f"Output index {idx}:")
    print(f"  Nombre: {output['name']}")
    print(f"  indice: {output['index']}")
    print(f"  Forma: {output['shape']}")
    print(f"  Tipo: {output['dtype']}")
    print()

# Opcionalmente, tambien puedes obtener los detalles de entrada
input_details = interpreter.get_input_details()
print("Detalles de las entradas del modelo:")
for idx, input in enumerate(input_details):
    print(f"Input index {idx}:")
    print(f"  Nombre: {input['name']}")
    print(f"  indice: {input['index']}")
    print(f"  Forma: {input['shape']}")
    print(f"  Tipo: {input['dtype']}")
    print()
