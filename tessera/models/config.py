"""
Pydantic models for config.yaml.
"""
from typing import Optional
from pydantic import BaseModel

from tessera.const import RUN_CONFIG_FILE
from tessera.models.common import load_and_validate_yaml


class TechNode(BaseModel):
    """
    Model for the technology node in config.yaml
    """
    catapult_lib_name: str
    vendor: str
    technology: str
    
    # ASIC specific
    lib_path: Optional[str] = None
    lib_db: Optional[str] = None
    catapult_lib_file: Optional[str] = None
    lib_verilog: Optional[str] = None
    lib_verilog_defines: Optional[str] = None

    # FPGA specific
    family: Optional[str] = None
    speed: Optional[str] = None
    part: Optional[str] = None


class RunConfig(BaseModel):
    """
    Load from config.yaml
    """
    total_threads: int
    threads_per_process: int
    min_free_gb: int
    frm: str
    to: str
    tools: dict[str, str] = {}
    tech: dict[str, TechNode] = {}

    @classmethod
    def load(cls, path=RUN_CONFIG_FILE):
        return load_and_validate_yaml(cls, path)
