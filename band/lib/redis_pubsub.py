from jsonrpcclient.async_client import AsyncClient
from jsonrpcclient.request import Request, Notification
from async_timeout import timeout
from collections import namedtuple
import asyncio
import ujson
import itertools
import aioredis
from aioredis.pubsub import Receiver
from aioredis.abc import AbcChannel

from .. import dome, logger, BROADCAST

# Positions in rpc method name
DEST_POS = 0
METHOD_POS = 1
SENDER_POS = 2


class MethodCall(namedtuple('MethodCall', ['dest', 'method', 'source'])):
    __slots__ = ()

    def tos(self):
        return self.dest + ':' + self.method + ':' + self.source

    def __repr__(self):
        return self.dest + ':' + self.method + ':' + self.source

    @classmethod
    def make(cls, method):
        return cls._make(method.split(':'))


class RedisPubSubRPC(AsyncClient):
    def __init__(self, name, app, redis_dsn, endpoint='none', **kwargs):
        super(RedisPubSubRPC, self).__init__(endpoint)
        self.name = name
        self._app = app
        self._loop = app.loop
        self.pending = {}
        self.redis_dsn = redis_dsn
        self.redis_params = kwargs.get("redis_params", {})
        self.channels = [self.name]
        if 'listen_all' in self.redis_params and self.redis_params['listen_all'] == True:
            self.channels.append(BROADCAST)
        self.queue = asyncio.Queue()
        self.timeout = 5
        self._pool = None
        self._mpsc = None

        self.id_gen = itertools.count(1)

    async def dispatch(self, msg):
        """
        add handling
        {"jsonrpc": "2.0", "error": {"code": -32602, "message": "Invalid params"}, "id": "1"}
        """
        # common extension
        if 'method' in msg:
            mparts = msg['method'].split(':')
            if len(mparts) == 3:
                msg['to'] = mparts[0]
                msg['method'] = mparts[1]
                msg['from'] = mparts[2]
        # answer
        if 'result' in msg:
            # logger.debug('received with result: %s', msg)
            if 'id' in msg and msg['id'] in self.pending:
                self.pending[msg['id']].set_result(msg)
        # call to served methods
        elif 'params' in msg:
            # check address structure
            if msg['to'] == self.name or msg['to'] == 'any':
                response = await dome.methods.dispatch(msg)
                if not response.is_notification:
                    await self.put(msg['from'], ujson.dumps(response))

    async def pool(self):
        if self._pool is None:
            logger.info('creating redis pool')
            self._pool = await aioredis.create_redis_pool(
                self.redis_dsn, loop=self._loop)
        return self._pool

    def mpsc(self):
        if self._mpsc is None:
            self._mpsc = Receiver(loop=self._loop)
        return self._mpsc

    async def reader(self):
        logger.info('redis_rpc_reader: entering connect loop')
        while True:
            try:
                # default sub
                pool = await self.pool()
                mpsc = self.mpsc()
                # sub = await aioredis.create_redis(self.redis_dsn, loop=app.loop)
                for chan in self.channels:
                    await pool.subscribe(mpsc.channel(chan))
                # sub = await aioredis.create_redis(self.redis_dsn, loop=app.loop)
                # ch, *_ = await sub.subscribe(self.name)
                logger.info('redis_rpc_reader: entering read loop')
                async for ch, msg in mpsc.iter():
                    # while await ch.wait_message():
                    # msg = await ch.get(encoding='utf-8')
                    try:
                        msg = ujson.loads(msg)
                        await self._app['scheduler'].spawn(self.dispatch(msg))
                    except Exception:
                        logger.exception('redis_rpc_reader: dispatching error')
            except aioredis.ConnectionClosedError:
                logger.exception('redis_rpc_reader: connection closed')
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info('redis_rpc_reader: loop cancelled')
                break
            except Exception:
                logger.exception('redis_rpc_reader: unknown error')
                await asyncio.sleep(1)
            finally:
                logger.debug('redis_rpc_reader: finally')
                if not pool.closed:
                    logger.debug('redis_rpc_reader: closing connection')
                    for chan in self.channels:
                        await pool.unsubscribe(chan)
                    mpsc.stop()
                    await pool.quit()
                    # await pool.wait_closed()
                    await asyncio.sleep(1)
                    break

    async def request(self, to, method, **params):
        mc = MethodCall(dest=to, method=method, source=self.name)
        req_id = str(next(self.id_gen))
        req = Request(mc.tos(), params, request_id=req_id)
        return await self.send(req, request_id=req['id'], to=to)

    async def notify(self, to, method, **params):
        mc = MethodCall(dest=to, method=method, source=self.name)
        req = Notification(mc.tos(), **params)
        return await self.send(req, to=to)

    async def put(self, dest, data):
        await self.queue.put((
            dest,
            data,
        ))

    async def send_message(self, request, **kwargs):
        to = kwargs['to']
        # Outbound msgs queue
        await self.put(to, request.encode())
        # skip waiting for notification
        if 'request_id' not in kwargs:
            return
        # Waiting for response
        req_id = kwargs['request_id']
        try:
            req = self.pending[req_id] = asyncio.Future()
            # await asyncio.wait_for(self.pending[req_id], timeout=self.timeout)
            async with timeout(5) as cm:
                await req
        except asyncio.TimeoutError:
            logger.error('rpc.send_message TimeoutError. to: %s ; id %s', to,
                         req_id)
        except asyncio.CancelledError:
            logger.error('CancelledError')
        finally:
            del self.pending[req_id]

        # Retunrning result
        return None if cm.expired else self.process_response(req.result())

    async def writer(self):
        while True:
            logger.info('redis_rpc_writer: entered root loop')
            try:
                pool = await self.pool()
                # pub = await aioredis.create_redis_pool(self.redis_dsn, loop=app.loop)
                logger.info('redis_rpc_writer: entering loop')
                while True:
                    name, msg = await self.queue.get()
                    self.queue.task_done()
                    # logger.debug('publishing to %s: %s', name, msg)
                    try:
                        await pool.publish(name, msg)
                    except Exception as error:
                        logger.error('redis_rpc_writer: error %s', error)

            except asyncio.CancelledError:
                logger.info('redis_rpc_writer: cancelled')
                break
            except Exception:
                logger.exception('redis_rpc_writer: unknown')
                await asyncio.sleep(1)
            finally:
                # await pool.quit()
                break

    async def get(self):
        item = await self.queue.get()
        self.queue.task_done()
        return item


# Attaching to aiohttp


async def redis_rpc_startup(app):
    app['rrpc_w'] = app.loop.create_task(app['rpc'].writer())
    app['rrpc_r'] = app.loop.create_task(app['rpc'].reader())


async def redis_rpc_cleanup(app):
    app['rrpc_r'].cancel()
    await app['rrpc_r']
    app['rrpc_w'].cancel()
    await app['rrpc_w']


def attach_redis_rpc(app, name, **kwargs):
    rpc = app['rpc'] = RedisPubSubRPC(name=name, app=app, **kwargs)
    app.on_startup.append(redis_rpc_startup)
    app.on_shutdown.append(redis_rpc_cleanup)
    return rpc


__all__ = ['RedisPubSubRPC', 'attach_redis_rpc']
