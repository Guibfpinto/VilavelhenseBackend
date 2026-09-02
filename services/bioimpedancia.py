import pandas as pd

def classif_imc(imc):
    if pd.isna(imc):
        return "indefinido"
    if imc < 20:
        return "baixo_peso"
    if imc < 24:
        return "normal"
    if imc < 27:
        return "sobrepeso_leve"
    if imc < 30:
        return "sobrepeso"
    return "obesidade"

def classif_gordura(p, idade):
    if pd.isna(p) or pd.isna(idade):
        return "indefinido"
    if idade < 30:
        if p < 12:
            return "excelente"
        if p < 17:
            return "bom"
        if p < 22:
            return "medio"
        return "alto"
    else:
        if p < 15:
            return "excelente"
        if p < 20:
            return "bom"
        if p < 25:
            return "medio"
        return "alto"

def estado_fisico(imc_class, gor_class):
    if imc_class == "indefinido" or gor_class == "indefinido":
        return "bom"
    if imc_class == "normal" and gor_class in ["excelente", "bom"]:
        return "otimo"
    if imc_class == "normal" and gor_class == "medio":
        return "bom"
    if imc_class in ["sobrepeso_leve", "sobrepeso"]:
        return "atencao"
    if imc_class == "obesidade" or gor_class == "alto":
        return "critico"
    return "regular"