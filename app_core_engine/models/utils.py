# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import logging
from typing import Any, Dict, List


def _initialize_tables(logger: logging.Logger) -> None:
    from .app import create_app_table
    from .thread import create_thread_table
    from .app_config import create_app_config_table

    create_app_table(logger)
    create_thread_table(logger)
    create_app_config_table(logger)



def _get_app_config(platform: str, app_id: str) -> Dict[str, Any]:
    from .app_config import get_app_config

    app_config = get_app_config(platform, app_id)

    return {
        "platform": app_config.platform,
        "app_id": app_config.app_id,
        "configruation": app_config.configuration
    }