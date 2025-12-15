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
from silvaengine_utility import Serializer

from ..types.app_config import AppConfigListType, AppConfigType
from .app import resolve_app_list

class AppIdIndex(LocalSecondaryIndex):
    """
    This class represents a local secondary index
    """

    class Meta:
        billing_mode = "PAY_PER_REQUEST"
        # All attributes are projected
        projection = AllProjection()
        index_name = "app_id-index"

    platform = UnicodeAttribute(hash_key=True)
    app_id = UnicodeAttribute(range_key=True)


class AppConfigModel(BaseModel):
    class Meta(BaseModel.Meta):
        table_name = "ace-app-configs"

    platform = UnicodeAttribute(hash_key=True)
    app_id = UnicodeAttribute(range_key=True)
    configuration = MapAttribute()
    created_at = UTCDateTimeAttribute()
    updated_at = UTCDateTimeAttribute()
    app_id_index = AppIdIndex()


def create_app_config_table(logger: logging.Logger) -> bool:
    """Create the App Config table if it doesn't exist."""
    if not AppConfigModel.exists():
        # Create with on-demand billing (PAY_PER_REQUEST)
        AppConfigModel.create_table(billing_mode="PAY_PER_REQUEST", wait=True)
        logger.info("The App Config table has been created.")
    return True


@retry(
    reraise=True,
    wait=wait_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
)
def get_app_config(platform: str, app_id: str) -> AppConfigModel:
    return AppConfigModel.get(platform, app_id)


def get_app_config_count(platform: str, app_id: str) -> int:
    return AppConfigModel.count(
        platform, AppConfigModel.app_id == app_id
    )


def get_app_config_type(info: ResolveInfo, app_config: AppConfigModel) -> AppConfigType:
    
    app_config = app_config.__dict__["attribute_values"]
    return AppConfigType(**Serializer.json_normalize(app_config))


def resolve_app_config(info: ResolveInfo, **kwargs: Dict[str, Any]) -> AppConfigType:
    # if "external_identifier" in kwargs:
    #     return get_app_type(
    #         info, _get_installed_app(kwargs["platform"], kwargs["external_identifier"])
    #     )

    count = get_app_config_count(kwargs["platform"], kwargs["app_id"])
    if count == 0:
        return None

    return get_app_config_type(
        info,
        get_app_config(kwargs["platform"], kwargs["app_id"]),
    )


@monitor_decorator
@resolve_list_decorator(
    attributes_to_get=["platform", "app_id"],
    list_type_class=AppConfigListType,
    type_funct=get_app_config_type,
)
def resolve_app_config_list(info: ResolveInfo, **kwargs: Dict[str, Any]) -> Any:
    platform = kwargs.get("platform")
    app_id = kwargs.get("app_id")
    # statuses = kwargs.get("statuses")

    args = []
    inquiry_funct = AppConfigModel.scan
    count_funct = AppConfigModel.count
    if platform:
        args = [platform, None]
        inquiry_funct = AppConfigModel.query
        if app_id:
            inquiry_funct = AppConfigModel.app_id_index.query
            args[1] = AppConfigModel.app_id == app_id
            count_funct = AppConfigModel.app_id_index.count

    the_filters = None  # We can add filters for the query.
    
    if the_filters is not None:
        args.append(the_filters)

    return inquiry_funct, count_funct, args


@insert_update_decorator(
    keys={
        "hash_key": "platform",
        "range_key": "app_id",
    },
    model_funct=get_app_config,
    count_funct=get_app_config_count,
    type_funct=get_app_config_type,
    range_key_required=True
    # data_attributes_except_for_data_diff=["created_at", "updated_at"],
    # activity_history_funct=None,
)
def insert_update_app_config(info: ResolveInfo, **kwargs: Dict[str, Any]) -> None:
    platform = kwargs.get("platform")
    app_id = kwargs.get("app_id")
    print(kwargs)
    if kwargs.get("entity") is None:
        cols = {
            "configuration": kwargs.get("configuration"),
            "created_at": pendulum.now("UTC"),
            "updated_at": pendulum.now("UTC"),
        }

        AppConfigModel(
            platform,
            app_id,
            **cols,
        ).save()
        return

    app_config = kwargs.get("entity")
    actions = [
        AppConfigModel.updated_at.set(pendulum.now("UTC")),
    ]

    # Map of kwargs keys to AppModel attributes
    field_map = {
        "configuration": AppConfigModel.configuration,
    }

    # Build actions dynamically based on the presence of keys in kwargs
    for key, field in field_map.items():
        if key in kwargs:  # Check if the key exists in kwargs
            actions.append(field.set(None if kwargs[key] == "null" else kwargs[key]))

    # Update the agent
    app_config.update(actions=actions)
    return


@delete_decorator(
    keys={
        "hash_key": "platform",
        "range_key": "app_id",
    },
    model_funct=get_app_config,
)
def delete_app_config(info: ResolveInfo, **kwargs: Dict[str, Any]) -> bool:
    installed_app_list = resolve_app_list(
        info,
        **{
            "platform": kwargs["entity"].platform,
            "app_id": kwargs["entity"].app_id,
            "status": ["installed"]
        },
    )
    if installed_app_list.total > 0:
        return False

    kwargs["entity"].delete()

    return True
