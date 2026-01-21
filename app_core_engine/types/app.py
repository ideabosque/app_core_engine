#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

from graphene import DateTime, Int, List, ObjectType, String
from silvaengine_dynamodb_base import ListObjectType
from silvaengine_utility import JSONCamelCase


class AppType(ObjectType):
    app_id = String()
    target_id = String()
    platform = String()
    access_token = String()
    scope = String()
    user_id = String()
    data = JSONCamelCase()
    status = String()
    created_at = DateTime()
    updated_at = DateTime()
    app_config = JSONCamelCase()


class AppListType(ListObjectType):
    app_list = List(AppType)
