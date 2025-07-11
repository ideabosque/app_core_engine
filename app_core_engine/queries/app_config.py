#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

from typing import Any, Dict

from graphene import ResolveInfo

from ..models import app_config
from ..types.app_config import AppConfigListType, AppConfigType


def resolve_app_config(info: ResolveInfo, **kwargs: Dict[str, Any]) -> AppConfigType:
    return app_config.resolve_app_config(info, **kwargs)


def resolve_app_config_list(info: ResolveInfo, **kwargs: Dict[str, Any]) -> AppConfigListType:
    return app_config.resolve_app_config_list(info, **kwargs)
