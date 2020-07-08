import threading
from concurrent import futures
from threading import Thread

import grpc
from google.protobuf.json_format import MessageToDict, ParseDict
from grpc import Server

# 初始化配置
from app.config import server_config
from app.grpc_template import route_pb2_grpc
from app.grpc_template.route_pb2 import AppStatus, ResponseList, DownloadInfo, Str, HttpRequestItem
from app.server.api import get_app_status, get_app_status_list, get_download_info
from app.server.client_proxy.client_proxy_manager import ClientProxyManager
from app.server.manager.data_manager import tl
from app.server.utils import logging, get_response


class Greeter(route_pb2_grpc.UpdateServerRouteServicer):

    def GetCloudConfig(self, request, context) -> Str:
        response = get_response(server_config.cloud_rule_hub_url)
        if response:
            logging.info("已完成获取云端配置仓库数据请求")
            return Str(s=response.text)

    def GetAppStatus(self, request, context) -> AppStatus:
        # noinspection PyBroadException
        try:
            request = MessageToDict(request, preserving_proto_field_name=True)
            hub_uuid: str = request['hub_uuid']
            if 'app_id' in request:
                app_id: list = request['app_id']
            else:
                app_id = []
            return self.__get_app_status(hub_uuid, app_id)
        except Exception:
            logging.exception('gRPC: GetAppStatus')
            return None

    def GetAppStatusList(self, request, context) -> ResponseList:
        # noinspection PyBroadException
        try:
            request = MessageToDict(request, preserving_proto_field_name=True)
            hub_uuid: str = request["hub_uuid"]
            app_id_list: list = [item['app_id'] for item in request["app_id_list"]]
            return self.__get_app_status_list(hub_uuid, app_id_list)
        except Exception:
            logging.exception('gRPC: GetAppStatusList')
            return None

    def GetDownloadInfo(self, request, context: grpc.RpcContext) -> DownloadInfo:
        if context.cancel():
            return
        # noinspection PyBroadException
        try:
            request = MessageToDict(request, preserving_proto_field_name=True)
            app_id_info = request["app_id_info"]
            hub_uuid = app_id_info["hub_uuid"]
            app_id = app_id_info["app_id"]
            asset_index = request["asset_index"]
            return self.__get_download_info(hub_uuid, app_id, asset_index)
        except Exception:
            logging.exception('gRPC: GetDownloadInfo')
            return None

    def NewClientProxyCall(self, request, context):
        # noinspection PyBroadException
        try:
            client_proxy = ClientProxyManager.new_client_proxy()
            yield ParseDict(client_proxy.get_first_request_item(), HttpRequestItem())  # 发送客户端 id
            for http_request in client_proxy:
                if http_request:
                    yield ParseDict(http_request, HttpRequestItem())
        except Exception:
            logging.exception('gRPC: NewClientProxyCall')

    def NewClientProxyReturn(self, request_iterator, context):
        client_proxy = None
        # noinspection PyBroadException
        try:
            for request in request_iterator:
                if request.code == 0:
                    index = int(request.key)
                    client_proxy = ClientProxyManager.get_client(index)
                else:
                    client_proxy.push_response(request.key, request.code, request.text)
        except Exception:
            ClientProxyManager.remove_proxy(client_proxy)
            logging.exception('gRPC: NewClientProxyReturn')

    @staticmethod
    def __get_app_status(hub_uuid: str, app_id: list) -> AppStatus:
        app_status = get_app_status(hub_uuid, app_id)
        if app_status is None:
            return AppStatus(valid_hub_uuid=False)
        return ParseDict(app_status, AppStatus())

    @staticmethod
    def __get_app_status_list(hub_uuid: str, app_id_list: list) -> ResponseList:
        app_status_list = get_app_status_list(hub_uuid, app_id_list)
        if app_status_list is None:
            app_status_list = {
                "response": [{"app_status": {"valid_hub_uuid": False}}]
            }
        return ParseDict(app_status_list, ResponseList())

    @staticmethod
    def __get_download_info(hub_uuid: str, app_id: list, asset_index: list) -> AppStatus:
        return ParseDict(get_download_info(hub_uuid, app_id, asset_index), DownloadInfo())


def init():
    if not server_config.debug_mode:
        tl.start()


def serve() -> [Thread, Server]:
    init()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=server_config.max_workers))
    route_pb2_grpc.add_UpdateServerRouteServicer_to_server(Greeter(), server)
    server.add_insecure_port(f'{server_config.host}:{server_config.port}')
    server.start()
    t = threading.Thread(target=server.wait_for_termination)
    t.start()
    return t, server