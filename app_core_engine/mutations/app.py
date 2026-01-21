# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import traceback
from typing import Any, Dict

from graphene import Boolean, Field, Int, Mutation, String

from silvaengine_utility import JSONCamelCase
from ..models.app import delete_app, insert_update_app
from ..types.app import AppType


class InsertUpdateApp(Mutation):
    app = Field(AppType)

    class Arguments:
        
        app_id = String(required=True)
        target_id = String(required=True)
        platform = String(required=True)
        access_token = String(required=True)
        user_id = String(required=False)
        scope = String(required=False)
        data = JSONCamelCase(required=True)
        status = String(required=False)

    @staticmethod
    def mutate(root: Any, info: Any, **kwargs: Dict[str, Any]) -> "InsertUpdateApp":
        try:
            app = insert_update_app(info, **kwargs)
        except Exception as e:
            log = traceback.format_exc()
            info.context.get("logger").error(log)
            raise e

        return InsertUpdateApp(app=app)


class DeleteApp(Mutation):
    ok = Boolean()

    class Arguments:
        app_id = String(required=True)
        target_id = String(required=True)
    @staticmethod
    def mutate(root: Any, info: Any, **kwargs: Dict[str, Any]) -> "DeleteApp":
        try:
            ok = delete_app(info, **kwargs)
        except Exception as e:
            log = traceback.format_exc()
            info.context.get("logger").error(log)
            raise e

        return DeleteApp(ok=ok)
