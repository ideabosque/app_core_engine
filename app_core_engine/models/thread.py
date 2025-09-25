#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import logging
import traceback
from typing import Any, Dict

import pendulum
from graphene import ResolveInfo
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute
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

from ..types.thread import ThreadListType, ThreadType


class UserIdIndex(LocalSecondaryIndex):
    """
    This class represents a local secondary index
    """

    class Meta:
        billing_mode = "PAY_PER_REQUEST"
        # All attributes are projected
        projection = AllProjection()
        index_name = "user_id-index"

    platform = UnicodeAttribute(hash_key=True)
    user_id = UnicodeAttribute(range_key=True)


class ThreadModel(BaseModel):
    class Meta(BaseModel.Meta):
        table_name = "ace-threads"

    platform = UnicodeAttribute(hash_key=True)
    thread_uuid = UnicodeAttribute(range_key=True)
    app_id = UnicodeAttribute()
    user_id = UnicodeAttribute()
    created_at = UTCDateTimeAttribute()
    user_id_index = UserIdIndex()


def create_thread_table(logger: logging.Logger) -> bool:
    """Create the Thread table if it doesn't exist."""
    if not ThreadModel.exists():
        # Create with on-demand billing (PAY_PER_REQUEST)
        ThreadModel.create_table(billing_mode="PAY_PER_REQUEST", wait=True)
        logger.info("The Thread table has been created.")
    return True


@retry(
    reraise=True,
    wait=wait_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
)
def get_thread(platform: str, thread_uuid: str) -> ThreadModel:
    return ThreadModel.get(platform, thread_uuid)


def get_thread_count(platform: str, thread_uuid: str) -> int:
    return ThreadModel.count(platform, ThreadModel.thread_uuid == thread_uuid)


def get_thread_type(info: ResolveInfo, thread: ThreadModel) -> ThreadType:
    thread = thread.__dict__["attribute_values"]
    return ThreadType(**Utility.json_normalize(thread))


def resolve_thread(info: ResolveInfo, **kwargs: Dict[str, Any]) -> ThreadType:
    count = get_thread_count(kwargs["platform"], kwargs["thread_uuid"])
    if count == 0:
        return None

    return get_thread_type(
        info, get_thread(kwargs["platform"], kwargs["thread_uuid"])
    )


@monitor_decorator
@resolve_list_decorator(
    attributes_to_get=["platform", "thread_uuid", "app_id", "user_id"],
    list_type_class=ThreadListType,
    type_funct=get_thread_type,
)
def resolve_thread_list(info: ResolveInfo, **kwargs: Dict[str, Any]) -> Any:
    platform = kwargs["platform"]
    user_id = kwargs.get("user_id", None)
    app_id = kwargs.get("app_id", None)
    created_at = kwargs.get("created_at", None)
    args = []
    inquiry_funct = ThreadModel.scan
    count_funct = ThreadModel.count
    if platform:
        args = [platform, None]
        inquiry_funct = ThreadModel.query
        if user_id:
            inquiry_funct = ThreadModel.user_id_index.query
            args[1] = ThreadModel.user_id == user_id
            count_funct = ThreadModel.user_id_index.count

    the_filters = None  # We can add filters for the query.
    if created_at:
        the_filters &= ThreadModel.created_at >= created_at
    
    if app_id:
        the_filters &= ThreadModel.app_id == app_id

    if the_filters is not None:
        args.append(the_filters)

    return inquiry_funct, count_funct, args


@insert_update_decorator(
    keys={
        "hash_key": "platform",
        "range_key": "thread_uuid",
    },
    model_funct=get_thread,
    count_funct=get_thread_count,
    type_funct=get_thread_type,
    range_key_required=True
    # data_attributes_except_for_data_diff=["created_at", "updated_at"],
    # activity_history_funct=None,
)
def insert_thread(info: ResolveInfo, **kwargs: Dict[str, Any]) -> None:
    platform = kwargs.get("platform")
    thread_uuid = kwargs.get("thread_uuid")
    if kwargs.get("entity") is None:
        cols = {
            "created_at": pendulum.now("UTC"),
        }
        for key in ["user_id", "app_id"]:
            if key in kwargs:
                cols[key] = kwargs[key]

        ThreadModel(
            platform,
            thread_uuid,
            **cols,
        ).save()
        return
    return


@delete_decorator(
    keys={
        "hash_key": "platform",
        "range_key": "thread_uuid",
    },
    model_funct=get_thread,
)
def delete_thread(info: ResolveInfo, **kwargs: Dict[str, Any]) -> bool:
    kwargs["entity"].delete()
    return True
