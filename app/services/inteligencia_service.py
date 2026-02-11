import pandas as pd
import catboost as cb
from thefuzz import fuzz, process

class InteligenciaService:
    def __init__(self):
        # Cargamos el motor de Crecimiento
        self.model_growth = cb.CatBoostClassifier()
        self.model_growth.load_model("models/maleon_predictor.cbm") 

        # Cargamos las bases de datos de servicios y seguridad
        self.df_servicios = pd.read_csv("data/prioridades_yucatan_maleon.csv", encoding='latin-1')
        self.df_seguridad = pd.read_csv("data/seguridad_municipios_maleon.csv")

    def limpiar_municipio(self, muni_usuario, pilar="servicios"):
        if not muni_usuario:
            return ""
        
        # Elegimos el dataframe correcto según lo que estemos buscando
        df = self.df_seguridad if pilar == "seguridad" else self.df_servicios
        nombres_reales = df['NOM_MUN'].unique().tolist()
        
        # Buscamos el parecido (ej: 'hoocaba' -> 'Hocabá')
        match, score = process.extractOne(muni_usuario, nombres_reales, scorer=fuzz.token_set_ratio)
        
        return match if score > 70 else muni_usuario