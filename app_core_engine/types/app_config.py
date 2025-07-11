#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

from graphene import DateTime, Int, List, ObjectType, String

from silvaengine_dynamodb_base import ListObjectType
from silvaengine_utility import JSON


class AppConfigType(ObjectType):
    platform = String()
    app_id = String()
    configuration = JSON()
    created_at = DateTime()
    updated_at = DateTime()


class AppConfigListType(ListObjectType):
    app_config_list = List(AppConfigType)
