import numpy as np
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
import tensorflow as tf
from tflite_model_maker.config import ExportFormat, QuantizationConfig
from tflite_model_maker import model_spec
from tflite_model_maker import object_detector
from tflite_support import metadata

assert tf.__version__.startswith('2')

# Configurar logging
tf.get_logger().setLevel('ERROR')
from absl import logging
logging.set_verbosity(logging.ERROR)

class MetricsLogger:
    def __init__(self, save_dir='./metrics'):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def save_metrics(self, metrics, prefix='evaluation'):
        """Guardar métricas en un archivo JSON"""
        # Convertir valores a tipo float para serialización JSON
        metrics_serializable = {k: float(v) if isinstance(v, (np.float32, np.float64, tf.float32)) else v
                                for k, v in metrics.items()}
        
        filename = f"{prefix}_metrics_{self.timestamp}.json"
        filepath = os.path.join(self.save_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(metrics_serializable, f, indent=4)
        
        print(f"Métricas guardadas en: {filepath}")
        return filepath

class MetricsVisualizer:
    @staticmethod
    def plot_ap_metrics(metrics):
        """Graficar métricas AP (Average Precision)"""
        ap_metrics = {k: v for k, v in metrics.items() if k.startswith('AP') and not k.startswith('AP_')}
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(ap_metrics.keys(), ap_metrics.values())
        plt.title('Average Precision Metrics')
        plt.xticks(rotation=45)
        plt.ylabel('Value')
        
        # Añadir valores sobre las barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.4f}',
                    ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_ar_metrics(metrics):
        """Graficar métricas AR (Average Recall)"""
        ar_metrics = {k: v for k, v in metrics.items() if k.startswith('AR')}
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(ar_metrics.keys(), ar_metrics.values())
        plt.title('Average Recall Metrics')
        plt.xticks(rotation=45)
        plt.ylabel('Value')
        
        # Añadir valores sobre las barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.4f}',
                    ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_class_performance(metrics):
        """Graficar rendimiento por clase"""
        class_metrics = {k: v for k, v in metrics.items() if k.startswith('AP_')}
        
        if class_metrics:  # Solo si hay métricas por clase
            plt.figure(figsize=(10, 6))
            bars = plt.bar(
                [k.split('/')[1] for k in class_metrics.keys()], 
                class_metrics.values()
            )
            plt.title('Performance por Clase (AP)')
            plt.ylabel('Average Precision')
            
            # Añadir valores sobre las barras
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.4f}',
                        ha='center', va='bottom')
            
            plt.tight_layout()
            plt.show()
    
    @staticmethod
    def plot_metrics_heatmap(metrics):
        """Crear un heatmap de todas las métricas"""
        # Reorganizar los datos para el heatmap
        metrics_df = pd.DataFrame([metrics]).T
        metrics_df.columns = ['value']
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(
            metrics_df,
            annot=True,
            fmt='.4f',
            cmap='YlOrRd',
            cbar_kws={'label': 'Value'}
        )
        plt.title('Metrics Heatmap')
        plt.tight_layout()
        plt.show()

class ModelTrainer:
    def __init__(self, train_images_dir, train_annotations_dir, 
                 val_images_dir, val_annotations_dir, classes):
        self.classes = classes
        
        # Cargar datos de entrenamiento y validación
        print("Cargando datos de entrenamiento...")
        self.train_data = object_detector.DataLoader.from_pascal_voc(
            train_images_dir,
            train_annotations_dir,
            classes
        )
        
        print("Cargando datos de validación...")
        self.val_data = object_detector.DataLoader.from_pascal_voc(
            val_images_dir,
            val_annotations_dir,
            classes
        )
        
        # Configurar el modelo
        print("Configurando el modelo...")
        self.spec = model_spec.get('efficientdet_lite0')
        
    def train(self, epochs=50, batch_size=4):
        """Entrenar el modelo y guardar los resultados de evaluación"""
        print(f"Iniciando entrenamiento con {epochs} épocas y batch size de {batch_size}...")
        
        self.model = object_detector.create(
            train_data=self.train_data,
            model_spec=self.spec,
            batch_size=batch_size,
            train_whole_model=True,
            epochs=epochs,
            validation_data=self.val_data
        )
        
        # Evaluar el modelo después del entrenamiento
        print("Evaluando el modelo después del entrenamiento...")
        self.final_metrics = self.model.evaluate(self.val_data)
    
    def export_model(self, export_dir='.', filename='model.tflite'):
        """Exportar el modelo a formato TFLite"""
        print(f"Exportando modelo a {os.path.join(export_dir, filename)}...")
        self.model.export(export_dir=export_dir, tflite_filename=filename)
        return os.path.join(export_dir, filename)
    
    def evaluate_and_print_metrics(self, tflite_model_path):
        """Evaluar el modelo y mostrar métricas"""
        print("\nEvaluando modelo TFLite...")
        eval_results = self.model.evaluate_tflite(tflite_model_path, self.val_data)
        
        # Inicializar el logger de métricas
        metrics_logger = MetricsLogger()
        
        # Combinar métricas finales y resultados de evaluación TFLite
        all_metrics = {}
        if hasattr(self, 'final_metrics'):
            all_metrics.update(self.final_metrics)
        all_metrics.update({k: v for k, v in eval_results.items() 
                          if isinstance(v, (int, float))})
        
        # Guardar métricas
        metrics_file = metrics_logger.save_metrics(all_metrics)
        
        # Imprimir métricas
        print("\nResultados de la evaluación final:")
        print("-" * 50)
        for metric_name, value in all_metrics.items():
            print(f"{metric_name}: {value:.4f}")
        
        # Visualizar métricas
        visualizer = MetricsVisualizer()
        visualizer.plot_ap_metrics(all_metrics)
        visualizer.plot_ar_metrics(all_metrics)
        visualizer.plot_class_performance(all_metrics)
        visualizer.plot_metrics_heatmap(all_metrics)
        
        return eval_results, metrics_file

def main():
    # Definir rutas y clases
    TRAIN_IMAGES_DIR = './DatasetVOC/train'
    TRAIN_ANNOTATIONS_DIR = './DatasetVOC/train'
    VAL_IMAGES_DIR = './DatasetVOC/validate'
    VAL_ANNOTATIONS_DIR = './DatasetVOC/validate'
    CLASSES = ['Mosca', 'Maleza', 'Mosaico']
    
    # Crear instancia del entrenador
    trainer = ModelTrainer(
        TRAIN_IMAGES_DIR,
        TRAIN_ANNOTATIONS_DIR,
        VAL_IMAGES_DIR,
        VAL_ANNOTATIONS_DIR,
        CLASSES
    )
    
    try:
        # Entrenar modelo
        trainer.train(epochs=60, batch_size=4)
        
        # Exportar modelo
        tflite_model_path = trainer.export_model(filename='model.tflite')
        
        # Evaluar modelo y generar visualizaciones
        evaluation_results, metrics_file = trainer.evaluate_and_print_metrics(tflite_model_path)
        
    except Exception as e:
        print(f"\nError durante el proceso: {str(e)}")
        raise

if __name__ == "__main__":
    main()