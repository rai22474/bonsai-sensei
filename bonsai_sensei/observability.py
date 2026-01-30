import os
from bonsai_sensei.logging_config import get_logger
from monocle_apptrace.instrumentation.common import setup_monocle_telemetry

logger = get_logger(__name__)


def setup_monocle_observability() -> bool:
    enabled = os.getenv("MONOCLE_ENABLED", "true").lower() == "true"
    if not enabled:
        return False
    
    workflow_name = os.getenv("MONOCLE_WORKFLOW_NAME", "bonsai-sensei")
    exporters = os.getenv("MONOCLE_EXPORTER", "console,file")
    setup_monocle_telemetry(
        workflow_name=workflow_name,
        monocle_exporters_list=exporters,
    )
    logger.info("Monocle observability enabled")
    
    return True
