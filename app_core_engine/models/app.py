#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import logging
import traceback
import uuid
from typing import Any, Dict

import pendulum
from graphene import ResolveInfo
from pynamodb.attributes import (
    MapAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import AllProjection, LocalSecondaryIndex
from tenacity import retry, stop_after_attempt, wait_exponential

from silvaengine_dynamodb_base import (
    BaseModel,
    delete_decorator,
    insert_update_decorator,
    monitor_decorator,
    resolve_list_decorator,
)
from silvaengine_utility import Utility

from ..types.app import AppListType, AppType
from .thread import resolve_thread_list
from .utils import _get_app_config

class TargetIdIndex(LocalSecondaryIndex):
    """
    This class represents a local secondary index
    """

    class Meta:
        billing_mode = "PAY_PER_REQUEST"
        # All attributes are projected
        projection = AllProjection()
        index_name = "target_id-index"

    app_id = UnicodeAttribute(hash_key=True)
    target_id = UnicodeAttribute(range_key=True)


class AppModel(BaseModel):
    class Meta(BaseModel.Meta):
        table_name = "ace-apps"

    app_id = UnicodeAttribute(hash_key=True)
    target_id = UnicodeAttribute(range_key=True)
    platform = UnicodeAttribute()
    access_token = UnicodeAttribute(null=True)
    scope = UnicodeAttribute()
    user_id = UnicodeAttribute()
    data = MapAttribute()
    status = UnicodeAttribute(default="installed")
    created_at = UTCDateTimeAttribute()
    updated_at = UTCDateTimeAttribute()
    target_id_index = TargetIdIndex()


def create_app_table(logger: logging.Logger) -> bool:
    """Create the Agent table if it doesn't exist."""
    if not AppModel.exists():
        # Create with on-demand billing (PAY_PER_REQUEST)
        AppModel.create_table(billing_mode="PAY_PER_REQUEST", wait=True)
        logger.info("The App table has been created.")
    return True


@retry(
    reraise=True,
    wait=wait_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
)
def get_app(app_id: str, target_id: str) -> AppModel:
    return AppModel.get(app_id, target_id)


@retry(
    reraise=True,
    wait=wait_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
)
def _get_installed_app(app_id: str, target_id: str) -> AppModel:
    try:
        results = AppModel.target_id_index.query(
            app_id,
            AppModel.target_id == target_id,
            filter_condition=(AppModel.status == "installed"),
            scan_index_forward=False,
            limit=1,
        )
        app = results.next()

        return app
    except StopIteration:
        return None


def get_app_count(app_id: str, target_id: str) -> int:
    return AppModel.count(
        app_id, AppModel.target_id == target_id
    )


def get_app_type(info: ResolveInfo, app: AppModel) -> AppType:
    try:
        app_config = _get_app_config(app.platform, app.app_id)
    except Exception as e:
        log = traceback.format_exc()
        info.context.get("logger").exception(log)
        raise e
    app = app.__dict__["attribute_values"]
    app["app_config"] = app_config
    return AppType(**Utility.json_loads(Utility.json_dumps(app)))


def resolve_app(info: ResolveInfo, **kwargs: Dict[str, Any]) -> AppType:

    count = get_app_count(kwargs["app_id"], kwargs["target_id"])
    if count == 0:
        return None

    return get_app_type(
        info,
        get_app(kwargs["app_id"], kwargs["target_id"]),
    )


@monitor_decorator
@resolve_list_decorator(
    attributes_to_get=["app_id", "target_id"],
    list_type_class=AppListType,
    type_funct=get_app_type,
)
def resolve_app_list(info: ResolveInfo, **kwargs: Dict[str, Any]) -> Any:
    platform = kwargs.get("platform")
    app_id = kwargs.get("app_id")
    target_id = kwargs.get("target_id")
    statuses = kwargs.get("statuses")

    args = []
    inquiry_funct = AppModel.scan
    count_funct = AppModel.count
    if app_id:
        args = [app_id, None]
        inquiry_funct = AppModel.query
        if target_id:
            inquiry_funct = AppModel.target_id_index.query
            args[1] = AppModel.target_id == target_id
            count_funct = AppModel.target_id_index.count

    the_filters = None  # We can add filters for the query.
    if platform:
        the_filters &= AppModel.platform == platform
    
    if statuses:
        the_filters &= AppModel.status.is_in(*statuses)

    if the_filters is not None:
        args.append(the_filters)

    return inquiry_funct, count_funct, args


def _uninstall_app(info: ResolveInfo, app_id: str, target_id: str) -> None:
    try:
        # Query for installed apps
        apps = AppModel.target_id_index.query(
            app_id,
            AppModel.target_id == target_id,
            filter_condition=AppModel.status == "installed",
        )
        # Update status to uninstalled
        for app in apps:
            app.status = "uninstalled"
            app.save()
        return
    except Exception as e:
        log = traceback.format_exc()
        info.context.get("logger").error(log)
        raise e
    
@insert_update_decorator(
    keys={
        "hash_key": "app_id",
        "range_key": "target_id",
    },
    model_funct=get_app,
    count_funct=get_app_count,
    type_funct=get_app_type,
    range_key_required=True,
    # data_attributes_except_for_data_diff=["created_at", "updated_at"],
    # activity_history_funct=None,
)
def insert_update_app(info: ResolveInfo, **kwargs: Dict[str, Any]) -> None:
    app_id = kwargs.get("app_id")
    target_id = kwargs.get("target_id")
    if kwargs.get("entity") is None:
        cols = {
            "platform": kwargs.get("platform"),
            "access_token": kwargs.get("access_token"),
            "user_id": kwargs.get("user_id"),
            "scope": kwargs.get("scope"),
            "data": kwargs.get("data", {}),
            "created_at": pendulum.now("UTC"),
            "updated_at": pendulum.now("UTC"),
        }

        AppModel(
            app_id,
            target_id,
            **cols,
        ).save()
        return

    app = kwargs.get("entity")
    actions = [
        AppModel.updated_at.set(pendulum.now("UTC")),
    ]

    if "status" in kwargs and (
        kwargs["status"] == "uninstalled" and app.status == "installed"
    ):
        _uninstall_app(info, app_id, app.target_id)

    # Map of kwargs keys to AppModel attributes
    field_map = {
        "access_token": AppModel.access_token,
        "user_id": AppModel.user_id,
        "scope": AppModel.scope,
        "data": AppModel.data,
        "status": AppModel.status,
    }

    # Build actions dynamically based on the presence of keys in kwargs
    for key, field in field_map.items():
        if key in kwargs:  # Check if the key exists in kwargs
            actions.append(field.set(None if kwargs[key] == "null" else kwargs[key]))

    # Update the agent
    app.update(actions=actions)
    return


@delete_decorator(
    keys={
        "hash_key": "app_id",
        "range_key": "target_id",
    },
    model_funct=get_app,
)
def delete_app(info: ResolveInfo, **kwargs: Dict[str, Any]) -> bool:
    thread_list = resolve_thread_list(
        info,
        **{
            "app_id": kwargs["entity"].app_id,
            "target_id": kwargs["entity"].target_id,
        },
    )
    if thread_list.total > 0:
        return False

    kwargs["entity"].delete()

    return True
