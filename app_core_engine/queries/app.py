#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

from typing import Any, Dict

from graphene import ResolveInfo

from ..models import app
from ..types.app import AppListType, AppType


def resolve_app(info: ResolveInfo, **kwargs: Dict[str, Any]) -> AppType:
    return app.resolve_app(info, **kwargs)


def resolve_app_list(info: ResolveInfo, **kwargs: Dict[str, Any]) -> AppListType:
    return app.resolve_app_list(info, **kwargs)
