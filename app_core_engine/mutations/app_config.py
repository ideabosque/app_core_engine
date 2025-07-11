# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import traceback
from typing import Any, Dict

from graphene import Boolean, Field, Int, Mutation, String

from silvaengine_utility import JSON

from ..models.app_config import delete_app_config, insert_update_app_config
from ..types.app_config import AppConfigType


class InsertUpdateAppConfig(Mutation):
    app_config = Field(AppConfigType)

    class Arguments:
        platform = String(required=True)
        app_id = String(required=True)
        configuration = JSON(required=True)

    @staticmethod
    def mutate(root: Any, info: Any, **kwargs: Dict[str, Any]) -> "InsertUpdateAppConfig":
        try:
            app_config = insert_update_app_config(info, **kwargs)
        except Exception as e:
            log = traceback.format_exc()
            info.context.get("logger").error(log)
            raise e

        return InsertUpdateAppConfig(app_config=app_config)


class DeleteAppConfig(Mutation):
    ok = Boolean()

    class Arguments:
        platform = String(required=True)
        app_id = String(required=True)
    @staticmethod
    def mutate(root: Any, info: Any, **kwargs: Dict[str, Any]) -> "DeleteAppConfig":
        try:
            ok = delete_app_config(info, **kwargs)
        except Exception as e:
            log = traceback.format_exc()
            info.context.get("logger").error(log)
            raise e

        return DeleteAppConfig(ok=ok)
