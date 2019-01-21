import getpass
import asyncio
import logging
import os
import configparser
import ssl
import time
from typing import List
from urllib.parse import urlencode
from weakref import WeakSet
from datetime import datetime
import aiohttp
from aiohttp import ClientError

from parsers import *


PROJ_DIR = os.path.dirname(os.path.abspath(__file__))

config = configparser.RawConfigParser()
config.read(os.path.join(PROJ_DIR, 'config.cfg'))

BASE_URL = config.get('studip', 'base_url')


class StudIPError(Exception):
    pass


class LoginError(StudIPError):
    pass


class StudIPScoreSession:
    def __init__(self, user, password, loop):
        self.user = user
        self.password = password
        self._studip_base = 'https://studip.uni-passau.de'
        self._sso_base = 'https://sso.uni-passau.de'

        self._background_tasks = WeakSet()  # TODO better management of (failing of) background tasks
        if not loop:
            self._loop = asyncio.get_event_loop()
        else:
            self._loop = loop

        context = ssl._create_unverified_context()

        connector = aiohttp.TCPConnector(loop=self._loop, limit=10,
                                         keepalive_timeout=30,
                                         force_close=False,
                                         ssl=context)
        self.ahttp = aiohttp.ClientSession(connector=connector, loop=self._loop,
                                           read_timeout=30,
                                           conn_timeout=30)

    def _sso_url(self, url):
        return self._sso_base + url


    def _studip_url(self, url):
        return self._studip_base + url


    async def close(self):
        try:
            for task in self._background_tasks:
                task.cancel()
        finally:
            if self.ahttp:
                await self.ahttp.close()

    async def do_login(self):
        try:
            async with self.ahttp.get(self._studip_url("/studip/index.php?again=yes&sso=shib")) as r:
                post_url = parse_login_form(await r.text())
        except (ClientError, ParserError) as e:
            raise LoginError("Could not initialize Shibboleth SSO login") from e

        try:
            async with self.ahttp.post(
                    self._sso_url(post_url),
                    data={
                        "j_username": self.user,
                        "j_password": self.password,
                        "uApprove.consent-revocation": "",
                        "_eventId_proceed": ""
                    }) as r:
                form_data = parse_saml_form(await r.text())
        except (ClientError, ParserError) as e:
            raise LoginError("Shibboleth SSO login failed") from e

        try:
            async with self.ahttp.post(self._studip_url("/Shibboleth.sso/SAML2/POST"), data=form_data) as r:
                await r.text()
                if not r.url.path.startswith("/studip"):
                    raise LoginError("Invalid redirect after Shibboleth SSO login to {}".format(r.url))
        except ClientError as e:
            raise LoginError("Could not complete Shibboleth SSO login") from e


    async def get_user_id(self):
        async with self.ahttp.get(self._studip_url("/studip/api.php/user")) as r:
            response = await r.json()
            return response['user_id']

    async def get_user_points(self, username):
        user_points = 0
        try:
            async with self.ahttp.get(self._studip_url("/studip/dispatch.php/profile?username={}".format(username))) as r:
                user_points = parse_user_points(await r.text())
        except (ClientError, ParserError) as e:
            raise StudIPError("Could not retrieve user score for user {}".format(username)) from e

        return user_points


def get_loop_session():
    username = config.get('studip', 'username')
    password = config.get('studip', 'password')

    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    session = StudIPScoreSession(username, password, event_loop)

    return event_loop, session


def get_points(username):
    event_loop, session = get_loop_session()
    points = None

    try:
        event_loop.run_until_complete(session.do_login())
        points = event_loop.run_until_complete(session.get_user_points(username))
    finally:
        async def shutdown_session_async(session):
            await session.close()

        event_loop.run_until_complete(shutdown_session_async(session))

    return points


def is_valid(username):
    # TODO: Implement
    return True


def get_rank(username):
    # TODO: Implement
    return None

