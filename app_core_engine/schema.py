#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import time
from typing import Any, Dict

from graphene import (
    Boolean,
    DateTime,
    Field,
    Int,
    List,
    ObjectType,
    ResolveInfo,
    String,
)

from .mutations.app_config import DeleteAppConfig, InsertUpdateAppConfig
from .mutations.app import DeleteApp, InsertUpdateApp
from .mutations.thread import DeleteThread, InsertThread
from .queries.app import resolve_app, resolve_app_list
from .queries.app_config import resolve_app_config, resolve_app_config_list
from .queries.thread import resolve_thread, resolve_thread_list
from .types.app import AppListType, AppType
from .types.app_config import AppConfigListType, AppConfigType
from .types.thread import ThreadListType, ThreadType


def type_class():
    return [
        AppConfigListType,
        AppConfigType,
        AppListType,
        AppType,
        ThreadType,
        ThreadListType,
    ]


class Query(ObjectType):
    ping = String()

    app_config = Field(
        AppConfigType,
        platform=String(required=True),
        app_id=String(required=True),
    )

    app_config_list = Field(
        AppConfigListType,
        page_number=Int(required=False),
        limit=Int(required=False),
        platform=String(required=False),
        app_id=String(required=False),
    )

    app = Field(
        AppType,
        app_id=String(required=True),
        target_id=String(required=True),
    )

    app_list = Field(
        AppListType,
        page_number=Int(required=False),
        limit=Int(required=False),
        app_id=String(required=False),
        target_id=String(required=False),
        platform=String(required=False),
        statuses=List(String, required=False),
    )

    thread = Field(
        ThreadType,
        platform=String(required=True),
        thread_uuid=String(required=True),
    )

    thread_list = Field(
        ThreadListType,
        page_number=Int(required=False),
        limit=Int(required=False),
        platform=String(required=True),
        app_id=String(required=False),
        user_id=String(required=False),
        created_at = DateTime(required=False)
    )

    def resolve_ping(self, info: ResolveInfo) -> str:
        return f"Hello at {time.strftime('%X')}!!"

    def resolve_app(self, info: ResolveInfo, **kwargs: Dict[str, Any]) -> AppType:
        return resolve_app(info, **kwargs)

    def resolve_app_list(
        self, info: ResolveInfo, **kwargs: Dict[str, Any]
    ) -> AppListType:
        return resolve_app_list(info, **kwargs)

    def resolve_app_config(self, info: ResolveInfo, **kwargs: Dict[str, Any]) -> AppConfigType:
        return resolve_app_config(info, **kwargs)

    def resolve_app_config_list(
        self, info: ResolveInfo, **kwargs: Dict[str, Any]
    ) -> AppConfigListType:
        return resolve_app_config_list(info, **kwargs)

    def resolve_thread(self, info: ResolveInfo, **kwargs: Dict[str, Any]) -> ThreadType:
        return resolve_thread(info, **kwargs)

    def resolve_thread_list(
        self, info: ResolveInfo, **kwargs: Dict[str, Any]
    ) -> ThreadListType:
        return resolve_thread_list(info, **kwargs)


class Mutations(ObjectType):
    insert_update_app = InsertUpdateApp.Field()
    delete_app = DeleteApp.Field()
    insert_update_app_config = InsertUpdateAppConfig.Field()
    delete_app_config = DeleteAppConfig.Field()
    insert_thread = InsertThread.Field()
    delete_thread = DeleteThread.Field()
