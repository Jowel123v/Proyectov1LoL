"""Script para eliminar y recrear todas las tablas de la base de datos"""
from utils.db import engine
from sqlmodel import SQLModel

# ¡IMPORTANTE! Importar TODOS los modelos ANTES de crear las tablas
from data.models import Champion, Team, MatchSummary, Player, MatchChampionLink

print("⚠️  ELIMINANDO todas las tablas...")

# Drop todas las tablas
SQLModel.metadata.drop_all(engine)

print("✅ Tablas eliminadas correctamente!")
print("📦 Creando tablas nuevamente con el esquema actualizado...")

# Crear todas las tablas nuevamente
SQLModel.metadata.create_all(engine)

print("✅ ¡Tablas creadas correctamente con el nuevo esquema!")
print("💡 Ahora puedes ejecutar 'python seed_worlds2024.py' para cargar los datos")
