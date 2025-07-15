#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import logging
from typing import Any, Dict, List

from graphene import Schema

from silvaengine_dynamodb_base import SilvaEngineDynamoDBBase
from silvaengine_utility import Utility

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


class AppCoreEngine(SilvaEngineDynamoDBBase):
    def __init__(self, logger: logging.Logger, **setting: Dict[str, Any]) -> None:
        SilvaEngineDynamoDBBase.__init__(self, logger, **setting)

        # Initialize configuration via the Config class
        Config.initialize(logger, **setting)

        self.logger = logger
        self.setting = setting

    # def ai_agent_build_graphql_query(self, **params: Dict[str, Any]):
    #     endpoint_id = params.get("endpoint_id")
    #     ## Test the waters 🧪 before diving in!
    #     ##<--Testing Data-->##
    #     if endpoint_id is None:
    #         endpoint_id = self.setting.get("endpoint_id")
    #     ##<--Testing Data-->##

    #     schema = Config.fetch_graphql_schema(
    #         self.logger,
    #         endpoint_id,
    #         params.get("function_name"),
    #         setting=self.setting,
    #     )
    #     return Utility.json_dumps(
    #         {
    #             "operation_name": params.get("operation_name"),
    #             "operation_type": params.get("operation_type"),
    #             "query": Utility.generate_graphql_operation(
    #                 params.get("operation_name"), params.get("operation_type"), schema
    #             ),
    #         }
    #     )

    def app_core_engine_graphql(self, **params: Dict[str, Any]) -> Any:
        schema = Schema(
            query=Query,
            mutation=Mutations,
            types=type_class(),
        )
        return self.graphql_execute(schema, **params)
