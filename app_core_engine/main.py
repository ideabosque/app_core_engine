#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import logging
from typing import Any, Dict, List

from graphene import Schema

from silvaengine_utility import Graphql
from silvaengine_dynamodb_base import BaseModel

from .handlers.config import Config
from .schema import Mutations, Query, type_class


# Hook function applied to deployment
def deploy() -> List:
    return [
        {
            "service": "App Core Engine",
            "class": "AppCoreEngine",
            "functions": {
                "app_core_engine_graphql": {
                    "is_static": False,
                    "label": "App Core Engine GraphQL",
                    "query": [
                        {"action": "ping", "label": "Ping"},
                        {
                            "action": "app",
                            "label": "View App",
                        },
                        {
                            "action": "appList",
                            "label": "View App List",
                        },
                        {
                            "action": "appConfig",
                            "label": "View App Config",
                        },
                        {
                            "action": "appConfigList",
                            "label": "View App Config List",
                        },
                        {
                            "action": "thread",
                            "label": "View Thread",
                        },
                        {
                            "action": "threadList",
                            "label": "View Thread List",
                        }
                    ],
                    "mutation": [
                        {
                            "action": "insertUpdateApp",
                            "label": "Create Update App",
                        },
                        {
                            "action": "deleteApp",
                            "label": "Delete App",
                        },
                        {
                            "action": "insertUpdateAppConfig",
                            "label": "Create Update App Config",
                        },
                        {
                            "action": "deleteAppConfig",
                            "label": "Delete App Config",
                        },
                        {
                            "action": "insertThread",
                            "label": "Create Update Thread",
                        },
                        {
                            "action": "deleteThread",
                            "label": "Delete Thread",
                        }
                    ],
                    "type": "RequestResponse",
                    "support_methods": ["POST"],
                    "is_auth_required": False,
                    "is_graphql": True,
                    "settings": "app_core_engine",
                    "disabled_in_resources": True,  # Ignore adding to resource list.
                }
            },
        }
    ]


class AppCoreEngine(Graphql):
    def __init__(self, logger: logging.Logger, **setting: Dict[str, Any]) -> None:
        Graphql.__init__(self, logger, **setting)

        if (
            setting.get("region_name")
            and setting.get("aws_access_key_id")
            and setting.get("aws_secret_access_key")
        ):
            BaseModel.Meta.region = setting.get("region_name")
            BaseModel.Meta.aws_access_key_id = setting.get("aws_access_key_id")
            BaseModel.Meta.aws_secret_access_key = setting.get("aws_secret_access_key")

        # Initialize configuration via the Config class
        Config.initialize(logger, **setting)

        self.logger = logger
        self.setting = setting

    def app_core_engine_graphql(self, **params: Dict[str, Any]) -> Any:
        schema = Schema(
            query=Query,
            mutation=Mutations,
            types=type_class(),
        )
        return self.execute(schema, **params)
