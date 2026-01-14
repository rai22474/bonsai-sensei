import logging
import sys

def configure_logging():
    """Configura el logging de la aplicación."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True # Forzar la reconfiguración si ya se ha configurado antes
    )
    
    # Ajustar niveles de log para librerías externas para reducir ruido
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger configurado."""
    return logging.getLogger(name)
